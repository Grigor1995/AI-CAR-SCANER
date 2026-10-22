import Foundation
import Network

/// Byte transport only. The backend owns initialization, PID selection/scaling.
actor NativeObdWifiBridge {
    private var connection: NWConnection?
    private var endpoint: String?
    private var initialized = false
    private var busy = false
    private let queue = DispatchQueue(label: "ai-car-scanner.obd-wifi")

    enum BridgeError: LocalizedError {
        case disconnected, invalidPort, concurrentRead, oversizedResponse, timeout
        var errorDescription: String? {
            switch self {
            case .disconnected: return "OBD adapter disconnected"
            case .invalidPort: return "Invalid adapter port"
            case .concurrentRead: return "An OBD read is already running"
            case .oversizedResponse: return "OBD response exceeded the transport limit"
            case .timeout: return "OBD adapter timed out"
            }
        }
    }

    func disconnect() {
        connection?.cancel()
        connection = nil
        endpoint = nil
        initialized = false
    }

    func poll(host: String, port: Int, api: DiagnosticAPI, sessionID: String? = nil) async throws -> ObdDecodedSnapshot {
        guard !busy else { throw BridgeError.concurrentRead }
        busy = true
        defer { busy = false }
        let target = "\(host):\(port)"
        if endpoint != target {
            disconnect()
            guard !host.isEmpty, let number = UInt16(exactly: port), number > 0,
                  let nwPort = NWEndpoint.Port(rawValue: number) else { throw BridgeError.invalidPort }
            let socket = NWConnection(host: NWEndpoint.Host(host), port: nwPort, using: .tcp)
            connection = socket
            do {
                try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
                    // State callbacks run on one serial queue. Clearing the handler
                    // before resuming guarantees a single continuation completion.
                    let deadline = DispatchWorkItem { socket.cancel() }
                    socket.stateUpdateHandler = { state in
                        switch state {
                        case .ready:
                            deadline.cancel()
                            socket.stateUpdateHandler = nil
                            continuation.resume()
                        case .failed(let error), .waiting(let error):
                            deadline.cancel()
                            socket.stateUpdateHandler = nil
                            socket.cancel()
                            continuation.resume(throwing: error)
                        case .cancelled:
                            deadline.cancel()
                            socket.stateUpdateHandler = nil
                            continuation.resume(throwing: BridgeError.disconnected)
                        default: break
                        }
                    }
                    socket.start(queue: queue)
                    queue.asyncAfter(deadline: .now()+10, execute: deadline)
                }
                endpoint = target
            } catch { disconnect(); throw error }
        }
        do {
            let plan = try await api.obdPlan()
            if !initialized {
                for command in plan.initialization { _ = try await exchange(command, timeout: 35) }
                initialized = true
            }
            var responses: [String: String] = [:]
            for command in plan.commands { responses[command] = try await exchange(command) }
            return try await api.decodeObd(responses, sessionID: sessionID)
        } catch {
            disconnect()
            throw error
        }
    }

    private func exchange(_ command: String, timeout: TimeInterval = 3) async throws -> String {
        try Task.checkCancellation()
        guard let socket = connection else { throw BridgeError.disconnected }
        // Cancellation closes the receive operation rather than leaving an
        // outstanding continuation or reusing a partially consumed response.
        return try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<String, Error>) in
                let deadline = DispatchWorkItem { socket.cancel() }
                queue.asyncAfter(deadline: .now()+timeout, execute: deadline)
                socket.send(content: Data((command+"\r").utf8), completion: .contentProcessed { error in
                    if let error { deadline.cancel(); continuation.resume(throwing: error); return }
                    self.queue.async {
                        self.receivePrompt(socket, accumulated: Data(), deadline: deadline, continuation: continuation)
                    }
                })
            }
        } onCancel: { socket.cancel() }
    }

    nonisolated private func receivePrompt(_ socket: NWConnection, accumulated: Data, deadline: DispatchWorkItem,
                                           continuation: CheckedContinuation<String, Error>) {
        socket.receive(minimumIncompleteLength: 1, maximumLength: 8192) { data, _, complete, error in
            if let error { deadline.cancel(); continuation.resume(throwing: error); return }
            var result = accumulated
            if let data { result.append(data) }
            if result.count > 16384 { deadline.cancel(); socket.cancel(); continuation.resume(throwing: BridgeError.oversizedResponse); return }
            if let end = result.firstIndex(of: 62) { // ELM '>' transport prompt.
                deadline.cancel()
                continuation.resume(returning: String(decoding: result[..<end], as: UTF8.self)); return
            }
            if complete { deadline.cancel(); continuation.resume(throwing: BridgeError.disconnected); return }
            self.receivePrompt(socket, accumulated: result, deadline: deadline, continuation: continuation)
        }
    }
}
