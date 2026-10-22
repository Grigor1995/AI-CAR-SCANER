package com.aicarscaner.mobile.data.obd

import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStream
import java.net.InetSocketAddress
import java.net.Socket

class WifiObdClient(private val initializationPlan: suspend () -> List<String> = {
    com.aicarscaner.mobile.data.api.ApiClient.diagnosticApi.obdPlan().initialization
}) {
    private val commandMutex = Mutex()
    private var socket: Socket? = null
    private var output: OutputStream? = null
    private var reader: BufferedReader? = null

    val isConnected: Boolean
        get() = socket?.isConnected == true && socket?.isClosed == false

    suspend fun connect(host: String, port: Int, timeoutMs: Int = 4000): Result<String> =
        withContext(Dispatchers.IO) {
            runCatching {
                close()
                val s = Socket()
                s.connect(InetSocketAddress(host.trim(), port), timeoutMs)
                socket = s
                output = s.getOutputStream()
                reader = BufferedReader(InputStreamReader(s.getInputStream(), Charsets.US_ASCII))
                initialize()
                "Connected to ${host}:${port}"
            }.onFailure { close() }
        }

    suspend fun command(command: String, timeoutMs: Long = 3000): Result<String> =
        withContext(Dispatchers.IO) {
            commandMutex.withLock {
            runCatching {
                val out = output ?: error("OBD Wi-Fi adapter is not connected")
                val input = reader ?: error("OBD Wi-Fi input is not available")
                out.write((command.trim() + "\r").toByteArray(Charsets.US_ASCII))
                out.flush()

                val deadline = System.currentTimeMillis() + timeoutMs
                val response = StringBuilder()
                while (System.currentTimeMillis() < deadline) {
                    kotlin.coroutines.coroutineContext.ensureActive()
                    while (input.ready()) {
                        val value = input.read()
                        if (value < 0) break
                        val ch = value.toChar()
                        if (ch == '>') return@runCatching clean(response.toString())
                        response.append(ch)
                    }
                    Thread.sleep(20)
                }
                throw java.net.SocketTimeoutException("OBD response prompt timed out")
            }.onFailure { close(); if (it is kotlinx.coroutines.CancellationException) throw it }
        }
        }

    suspend fun readRpm(): Result<String> = command("010C")
    suspend fun readDtcs(): Result<String> = command("03")

    fun close() {
        runCatching { socket?.close() }
        socket = null
        output = null
        reader = null
    }

    private suspend fun initialize() {
        for (step in initializationPlan()) command(step, 35000).getOrThrow()
    }

    private fun clean(value: String): String =
        value.replace("SEARCHING...", "", ignoreCase = true).trim()
}
