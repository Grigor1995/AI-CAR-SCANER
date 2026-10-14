package com.aicarscaner.mobile.data.obd

import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import java.nio.charset.StandardCharsets
import java.util.concurrent.CopyOnWriteArrayList
import kotlin.concurrent.thread

class WifiObdClientTest {
    @Test
    fun connectsInitializesAdapterAndSanitizesCommandResponses() = runTest {
        FakeElmServer().use { server ->
            val client = WifiObdClient()
            try {
                val connection = client.connect("127.0.0.1", server.port, timeoutMs = 1_000)

                assertTrue(connection.isSuccess)
                assertEquals("Connected to 127.0.0.1:${server.port}", connection.getOrThrow())
                assertTrue(client.isConnected)

                val rpm = client.command(" 010C ")
                assertTrue(rpm.isSuccess)
                assertEquals("410C1AF8", rpm.getOrThrow())

                val dtcs = client.readDtcs()
                assertTrue(dtcs.isSuccess)
                assertEquals("430102", dtcs.getOrThrow())

                assertTrue(server.commands.containsAll(listOf("ATZ", "ATE0", "ATL0", "ATS0", "ATSP0", "010C", "03")))
            } finally {
                client.close()
            }

            assertFalse(client.isConnected)
            val afterClose = client.command("010C")
            assertTrue(afterClose.isFailure)
            assertEquals("OBD Wi-Fi adapter is not connected", afterClose.exceptionOrNull()?.message)
        }
    }

    @Test
    fun invalidPortReturnsFailureAndLeavesClientDisconnected() = runTest {
        val client = WifiObdClient()

        val result = client.connect("127.0.0.1", -1, timeoutMs = 100)

        assertTrue(result.isFailure)
        assertFalse(client.isConnected)
        client.close()
        assertFalse(client.isConnected)
    }

    /**
     * Small in-process ELM327-style TCP endpoint. It replies to adapter setup commands
     * and emits representative RPM/DTC responses for command-contract tests.
     */
    private class FakeElmServer : AutoCloseable {
        private val server = ServerSocket(0, 1, InetAddress.getByName("127.0.0.1"))
        val port: Int = server.localPort
        val commands = CopyOnWriteArrayList<String>()
        @Volatile private var closing = false

        private val worker = thread(name = "fake-elm327-server", isDaemon = true) {
            try {
                server.accept().use { socket: Socket ->
                    val input = socket.getInputStream()
                    val output = socket.getOutputStream()
                    val commandBuffer = StringBuilder()
                    while (!closing) {
                        val next = input.read()
                        if (next < 0) break
                        when (next) {
                            13 -> {
                                val command = commandBuffer.toString().trim()
                                commandBuffer.setLength(0)
                                commands.add(command)
                                val response = when (command.uppercase()) {
                                    "010C" -> "SEARCHING...\\r410C1AF8\\r>"
                                    "03" -> "430102\\r>"
                                    else -> "OK\\r>"
                                }
                                output.write(response.toByteArray(StandardCharsets.US_ASCII))
                                output.flush()
                            }
                            10 -> Unit
                            else -> commandBuffer.append(next.toChar())
                        }
                    }
                }
            } catch (_: Exception) {
                // Socket closure is expected when a test finishes.
            }
        }

        override fun close() {
            closing = true
            runCatching { server.close() }
            worker.join(1_000)
        }
    }
}
