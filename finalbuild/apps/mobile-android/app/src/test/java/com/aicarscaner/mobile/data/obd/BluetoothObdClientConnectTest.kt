package com.aicarscaner.mobile.data.obd

import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothSocket
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.util.UUID

class BluetoothObdClientConnectTest {
    @Test
    fun socketConnectFailureClosesPendingSocketAndLeavesClientDisconnected() = runTest {
        val device = mockk<BluetoothDevice>()
        val socket = mockk<BluetoothSocket>()
        every { device.createRfcommSocketToServiceRecord(any<UUID>()) } returns socket
        every { socket.connect() } throws IOException("Bluetooth connect failed")
        every { socket.close() } returns Unit

        val client = BluetoothObdClient()
        val result = client.connect(device)

        assertTrue(result.isFailure)
        assertEquals("Bluetooth connect failed", result.exceptionOrNull()?.message)
        assertFalse(client.isConnected)
        verify(exactly = 1) { socket.close() }
    }

    @Test
    fun successfulConnectionInitializesAdapterReadsPidsAndClosesSocket() = runTest {
        val device = mockk<BluetoothDevice>()
        val socket = mockk<BluetoothSocket>()
        val commands = ByteArrayOutputStream()
        val replies = ByteArrayInputStream(
            ("OK\r>".repeat(5) + "SEARCHING...\r410C1AF8\r>" + "430102\r>")
                .toByteArray(Charsets.US_ASCII)
        )

        every { device.createRfcommSocketToServiceRecord(any<UUID>()) } returns socket
        every { device.name } returns "ELM327"
        every { socket.connect() } returns Unit
        every { socket.isConnected } returns true
        every { socket.inputStream } returns replies
        every { socket.outputStream } returns commands
        every { socket.close() } returns Unit

        val client = BluetoothObdClient()
        val connected = client.connect(device)

        assertTrue(connected.isSuccess)
        assertEquals("Connected to ELM327", connected.getOrThrow())
        assertTrue(client.isConnected)
        assertEquals("410C1AF8", client.readPid010c().getOrThrow())
        assertEquals("430102", client.readDtcs().getOrThrow())
        assertEquals(
            "ATZ\rATE0\rATL0\rATS0\rATSP0\r010C\r03\r",
            commands.toString("US-ASCII")
        )

        client.close()
        assertFalse(client.isConnected)
        verify(exactly = 1) { socket.close() }
    }

    @Test
    fun socketCreationFailureIsReturnedAsFailure() = runTest {
        val device = mockk<BluetoothDevice>()
        every { device.createRfcommSocketToServiceRecord(any<UUID>()) } throws
            IOException("RFCOMM socket unavailable")

        val client = BluetoothObdClient()
        val result = client.connect(device)

        assertTrue(result.isFailure)
        assertEquals("RFCOMM socket unavailable", result.exceptionOrNull()?.message)
        assertFalse(client.isConnected)
    }
}
