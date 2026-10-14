package com.aicarscaner.mobile.data.obd

import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothSocket
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.IOException
import java.util.UUID

class BluetoothObdClient {
    companion object {
        private val SPP_UUID: UUID =
            UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
    }

    private var socket: BluetoothSocket? = null

    val isConnected: Boolean
        get() = socket?.isConnected == true

    suspend fun connect(device: BluetoothDevice): Result<String> = withContext(Dispatchers.IO) {
        var pendingSocket: BluetoothSocket? = null
        runCatching {
            close()
            val s = device.createRfcommSocketToServiceRecord(SPP_UUID)
            pendingSocket = s
            s.connect()
            socket = s
            pendingSocket = null

            initialize()
            "Connected to ${device.name ?: device.address}"
        }.onFailure {
            // A connect failure happens before the socket is stored on this client.
            // Close the local socket explicitly so failed attempts do not leak it.
            pendingSocket?.let { pending -> runCatching { pending.close() } }
            close()
        }
    }

    suspend fun command(command: String, timeoutMs: Long = 2500): Result<String> =
        withContext(Dispatchers.IO) {
            runCatching {
                val s = socket ?: error("OBD adapter is not connected")
                s.outputStream.write((command.trim() + "\r").toByteArray(Charsets.US_ASCII))
                s.outputStream.flush()

                val deadline = System.currentTimeMillis() + timeoutMs
                val buffer = StringBuilder()
                while (System.currentTimeMillis() < deadline) {
                    while (s.inputStream.available() > 0) {
                        val value = s.inputStream.read()
                        if (value < 0) break
                        val ch = value.toChar()
                        if (ch == '>') return@runCatching sanitize(buffer.toString())
                        if (ch != '\r' && ch != '\n') buffer.append(ch)
                    }
                    Thread.sleep(20)
                }
                sanitize(buffer.toString())
            }
        }

    suspend fun readPid010c(): Result<String> = command("010C")

    suspend fun readDtcs(): Result<String> = command("03")

    fun close() {
        try {
            socket?.close()
        } catch (_: IOException) {
        } finally {
            socket = null
        }
    }

    private suspend fun initialize() {
        command("ATZ", 4000)
        command("ATE0")
        command("ATL0")
        command("ATS0")
        command("ATSP0")
    }

    private fun sanitize(value: String): String =
        value.replace("SEARCHING...", "", ignoreCase = true).trim()
}