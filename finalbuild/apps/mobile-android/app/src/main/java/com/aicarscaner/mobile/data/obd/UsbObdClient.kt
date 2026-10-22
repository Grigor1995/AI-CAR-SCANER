package com.aicarscaner.mobile.data.obd

import android.hardware.usb.UsbConstants
import android.hardware.usb.UsbDevice
import android.hardware.usb.UsbDeviceConnection
import android.hardware.usb.UsbEndpoint
import android.hardware.usb.UsbInterface
import android.hardware.usb.UsbManager
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class UsbObdClient(private val initializationPlan: suspend () -> List<String> = {
    com.aicarscaner.mobile.data.api.ApiClient.diagnosticApi.obdPlan().initialization
}) {
    private val commandMutex = Mutex()
    private var connection: UsbDeviceConnection? = null
    private var usbInterface: UsbInterface? = null
    private var inEndpoint: UsbEndpoint? = null
    private var outEndpoint: UsbEndpoint? = null

    val isConnected: Boolean
        get() = connection != null && usbInterface != null && inEndpoint != null && outEndpoint != null

    suspend fun connect(usbManager: UsbManager, device: UsbDevice): Result<String> =
        withContext(Dispatchers.IO) {
            runCatching {
                close()
                check(usbManager.hasPermission(device)) {
                    "USB permission is required for ${device.deviceName}"
                }

                val candidate = findBulkInterface(device)
                    ?: error("No bulk USB serial interface found on ${device.deviceName}")
                val input = candidate.first
                val output = candidate.second
                val handle = usbManager.openDevice(device)
                    ?: error("Unable to open USB device ${device.deviceName}")

                // Keep the handle reachable by close() while claiming the interface so
                // the failure path can close a device that could not be claimed.
                connection = handle
                usbInterface = candidate.third
                check(handle.claimInterface(candidate.third, true)) {
                    "Unable to claim USB interface"
                }

                inEndpoint = input
                outEndpoint = output

                initialize()
                "Connected to USB ${device.productName ?: device.deviceName}"
            }.onFailure { close() }
        }

    suspend fun command(command: String, timeoutMs: Long = 3000): Result<String> =
        withContext(Dispatchers.IO) {
            commandMutex.withLock {
            runCatching {
                val handle = connection ?: error("USB OBD adapter is not connected")
                val input = inEndpoint ?: error("USB input endpoint is not available")
                val output = outEndpoint ?: error("USB output endpoint is not available")

                val data = (command.trim() + "\r").toByteArray(Charsets.US_ASCII)
                check(handle.bulkTransfer(output, data, data.size, 2000) >= 0) {
                    "USB write failed"
                }

                val buffer = ByteArray(512)
                val response = StringBuilder()
                val deadline = System.currentTimeMillis() + timeoutMs
                while (System.currentTimeMillis() < deadline) {
                    kotlin.coroutines.coroutineContext.ensureActive()
                    val count = handle.bulkTransfer(input, buffer, buffer.size, 250)
                    if (count > 0) {
                        val chunk = String(buffer, 0, count, Charsets.US_ASCII)
                        for (ch in chunk) {
                            if (ch == '>') return@runCatching clean(response.toString())
                            response.append(ch)
                        }
                    }
                }
                throw java.net.SocketTimeoutException("OBD response prompt timed out")
            }.onFailure { close(); if (it is kotlinx.coroutines.CancellationException) throw it }
        }
        }

    suspend fun readRpm(): Result<String> = command("010C")
    suspend fun readDtcs(): Result<String> = command("03")

    fun close() {
        runCatching {
            usbInterface?.let { connection?.releaseInterface(it) }
            connection?.close()
        }
        connection = null
        usbInterface = null
        inEndpoint = null
        outEndpoint = null
    }

    private suspend fun initialize() {
        for (step in initializationPlan()) command(step, 35000).getOrThrow()
    }

    private fun clean(value: String): String =
        value.replace("SEARCHING...", "", ignoreCase = true).trim()

    private fun findBulkInterface(
        device: UsbDevice
    ): Triple<UsbEndpoint, UsbEndpoint, UsbInterface>? {
        for (i in 0 until device.interfaceCount) {
            val intf = device.getInterface(i)
            var input: UsbEndpoint? = null
            var output: UsbEndpoint? = null
            for (j in 0 until intf.endpointCount) {
                val endpoint = intf.getEndpoint(j)
                if (endpoint.type != UsbConstants.USB_ENDPOINT_XFER_BULK) continue
                if (endpoint.direction == UsbConstants.USB_DIR_IN) input = endpoint
                if (endpoint.direction == UsbConstants.USB_DIR_OUT) output = endpoint
            }
            if (input != null && output != null) {
                return Triple(input, output, intf)
            }
        }
        return null
    }
}