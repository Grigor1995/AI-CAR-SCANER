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
            val client = WifiObdClient(initializationPlan = { backendInitializationFixture })
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
    fun commandWithoutPromptFailsAndClosesConnection() = runTest {
        FakeElmServer(partialResponseFor = "010C").use { server ->
            val client = WifiObdClient(initializationPlan = { backendInitializationFixture })
            try {
                assertTrue(client.connect("127.0.0.1", server.port, timeoutMs = 1_000).isSuccess)

                // A truncated ELM327 frame must not leave the command loop hanging forever.
                val partial = client.command("010C", timeoutMs = 700)
                assertTrue(partial.isFailure)
                assertTrue(partial.exceptionOrNull() is java.net.SocketTimeoutException)

                // A late reply must not be reused as the next command's response.
                assertFalse(client.isConnected)
                assertTrue(client.readDtcs().isFailure)
            } finally {
                client.close()
            }
            assertFalse(client.isConnected)
        }
    }

    @Test
    fun invalidPortReturnsFailureAndLeavesClientDisconnected() = runTest {
        val client = WifiObdClient(initializationPlan = { backendInitializationFixture })

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
    private class FakeElmServer(private val partialResponseFor: String? = null) : AutoCloseable {
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
                                    "010C" -> "SEARCHING...\r410C1AF8\r>"
                                    "03" -> "430102\r>"
                                    else -> "OK\r>"
                                }
                                val payload = if (command.equals(partialResponseFor, ignoreCase = true)) {
                                    response.removeSuffix(">")
                                } else {
                                    response
                                }
                                output.write(payload.toByteArray(StandardCharsets.US_ASCII))
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
