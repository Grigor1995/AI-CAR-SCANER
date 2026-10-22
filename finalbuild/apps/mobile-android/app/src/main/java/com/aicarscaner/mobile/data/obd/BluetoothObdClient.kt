package com.aicarscaner.mobile.data.obd

import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothSocket
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.IOException
import java.util.UUID

class BluetoothObdClient(private val initializationPlan: suspend () -> List<String> = {
    com.aicarscaner.mobile.data.api.ApiClient.diagnosticApi.obdPlan().initialization
}) {
    private val commandMutex = Mutex()
    companion object {
        private val SPP_UUID: UUID =
            UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
    }

    private var socket: BluetoothSocket? = null

    val isConnected: Boolean
        get() = socket?.isConnected == true

    suspend fun connect(device: BluetoothDevice): Result<String> = withContext(Dispatchers.IO) {
        var pendingSocket: BluetoothSocket? = null
        fun cleanUpFailedConnection() {
            pendingSocket?.let { pending -> runCatching { pending.close() } }
            close()
        }
        try {
            close()
            val s = device.createRfcommSocketToServiceRecord(SPP_UUID)
            pendingSocket = s
            s.connect()
            socket = s
            pendingSocket = null
            initialize()
            Result.success("Connected to ${device.name ?: device.address}")
        } catch (cancelled: CancellationException) {
            cleanUpFailedConnection()
            throw cancelled
        } catch (denied: SecurityException) {
            // Permission may be revoked after the screen checks it.
            cleanUpFailedConnection()
            Result.failure(denied)
        } catch (error: Exception) {
            cleanUpFailedConnection()
            Result.failure(error)
        }
    }

    suspend fun command(command: String, timeoutMs: Long = 2500): Result<String> =
        withContext(Dispatchers.IO) {
            commandMutex.withLock {
            runCatching {
                val s = socket ?: error("OBD adapter is not connected")
                s.outputStream.write((command.trim() + "\r").toByteArray(Charsets.US_ASCII))
                s.outputStream.flush()

                val deadline = System.currentTimeMillis() + timeoutMs
                val buffer = StringBuilder()
                while (System.currentTimeMillis() < deadline) {
                    kotlin.coroutines.coroutineContext.ensureActive()
                    while (s.inputStream.available() > 0) {
                        val value = s.inputStream.read()
                        if (value < 0) break
                        val ch = value.toChar()
                        if (ch == '>') return@runCatching sanitize(buffer.toString())
                        buffer.append(ch)
                    }
                    Thread.sleep(20)
                }
                throw java.net.SocketTimeoutException("OBD response prompt timed out")
            }.onFailure { close(); if (it is kotlinx.coroutines.CancellationException) throw it }
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
        for (step in initializationPlan()) command(step, 35000).getOrThrow()
    }

    private fun sanitize(value: String): String =
        value.replace("SEARCHING...", "", ignoreCase = true).trim()
}