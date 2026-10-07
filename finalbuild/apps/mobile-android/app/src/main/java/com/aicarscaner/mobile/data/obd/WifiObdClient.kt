package com.aicarscaner.mobile.data.obd

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStream
import java.net.InetSocketAddress
import java.net.Socket

class WifiObdClient {
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
            runCatching {
                val out = output ?: error("OBD Wi-Fi adapter is not connected")
                val input = reader ?: error("OBD Wi-Fi input is not available")
                out.write((command.trim() + "\r").toByteArray(Charsets.US_ASCII))
                out.flush()

                val deadline = System.currentTimeMillis() + timeoutMs
                val response = StringBuilder()
                while (System.currentTimeMillis() < deadline) {
                    while (input.ready()) {
                        val value = input.read()
                        if (value < 0) break
                        val ch = value.toChar()
                        if (ch == '>') return@runCatching clean(response.toString())
                        if (ch != '\r' && ch != '\n') response.append(ch)
                    }
                    Thread.sleep(20)
                }
                clean(response.toString())
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
        command("ATZ", 4000)
        command("ATE0")
        command("ATL0")
        command("ATS0")
        command("ATSP0")
    }

    private fun clean(value: String): String =
        value.replace("SEARCHING...", "", ignoreCase = true).trim()
