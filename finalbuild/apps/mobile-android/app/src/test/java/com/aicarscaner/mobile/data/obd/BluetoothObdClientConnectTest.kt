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
