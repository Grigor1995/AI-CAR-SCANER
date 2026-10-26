import Foundation
import Network

/// Byte transport only. The backend owns initialization, PID selection/scaling.
actor NativeObdWifiBridge {
    private var connection: NWConnection?
    private var endpoint: String?
    private var initialized = false
    private var liveSessionID: String?
    private var liveCommands: [String]?
    private var capabilityFrames: [String:String] = [:]
    private var busy = false
    private let queue = DispatchQueue(label: "ai-car-scanner.obd-wifi")

    enum BridgeError: LocalizedError {
        case disconnected, invalidPort, concurrentRead, oversizedResponse, timeout, capabilityUnavailable, noSupportedChannels
        var errorDescription: String? {
            switch self {
            case .disconnected: return "OBD adapter disconnected"
            case .invalidPort: return "Invalid adapter port"
            case .concurrentRead: return "An OBD read is already running"
            case .oversizedResponse: return "OBD response exceeded the transport limit"
            case .timeout: return "OBD adapter timed out"
            case .capabilityUnavailable: return "Backend capability discovery plan is unavailable"
            case .noSupportedChannels: return "Vehicle reports no supported live channels"
            }
        }
        func message(language: AppLanguage) -> String {
            let translated: (String,String)
            switch self {
            case .capabilityUnavailable:
                translated=("Backend-ի աջակցվող PID-երի հայտնաբերման պլանը հասանելի չէ", "План определения поддерживаемых PID недоступен на сервере")
            case .noSupportedChannels:
                translated=("Մեքենան չի հայտնել աջակցվող ընթացիկ տվյալների ալիքներ", "Автомобиль не сообщил о поддерживаемых каналах текущих данных")
            default: return errorDescription ?? "OBD error"
            }
            switch language {
            case .hy: return translated.0
            case .ru: return translated.1
            case .en: return errorDescription ?? "OBD error"
            }
        }

    }

    func disconnect() {
        connection?.cancel()
        connection = nil
        endpoint = nil
        initialized = false
        liveSessionID = nil
        liveCommands = nil
        capabilityFrames = [:]
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
            if liveSessionID != sessionID {
                liveCommands = nil
                capabilityFrames = [:]
                liveSessionID = sessionID
            }
            if liveCommands == nil {
                let bootstrap = try await api.obdPlan()
                if !initialized {
                    for command in bootstrap.initialization { _ = try await exchange(command, timeout: 35) }
                    initialized = true
                }
                guard let discovery=bootstrap.discovery, !discovery.isEmpty else { throw BridgeError.capabilityUnavailable }
                var observed: [String:String] = [:]
                for command in discovery { observed[command] = try await exchange(command, timeout:35) }
                let selected = try await api.supportedObdPlan(observed)
                guard !selected.commands.isEmpty else { throw BridgeError.noSupportedChannels }
                capabilityFrames = observed
                liveCommands = selected.commands
            }
            var responses = capabilityFrames
            for command in liveCommands ?? [] { responses[command] = try await exchange(command) }
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
