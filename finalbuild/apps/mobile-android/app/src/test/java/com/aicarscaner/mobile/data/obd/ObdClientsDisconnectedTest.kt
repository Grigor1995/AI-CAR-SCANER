package com.aicarscaner.mobile.data.obd

import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ObdClientsDisconnectedTest {
    @Test
    fun bluetoothCommandsFailClearlyWhenNotConnected() = runTest {
        val client = BluetoothObdClient()

        assertFalse(client.isConnected)
        assertEquals("OBD adapter is not connected", client.command("010C").exceptionOrNull()?.message)
        assertEquals("OBD adapter is not connected", client.readPid010c().exceptionOrNull()?.message)
        assertEquals("OBD adapter is not connected", client.readDtcs().exceptionOrNull()?.message)
        client.close()
        assertFalse(client.isConnected)
    }

    @Test
    fun wifiCommandsFailClearlyWhenNotConnected() = runTest {
        val client = WifiObdClient()

        assertFalse(client.isConnected)
        val rpm = client.readRpm()
        val dtcs = client.readDtcs()
        assertTrue(rpm.isFailure)
        assertEquals("OBD Wi-Fi adapter is not connected", rpm.exceptionOrNull()?.message)
        assertTrue(dtcs.isFailure)
        assertEquals("OBD Wi-Fi adapter is not connected", dtcs.exceptionOrNull()?.message)
        client.close()
        assertFalse(client.isConnected)
    }

    @Test
    fun usbCommandsFailClearlyWhenNotConnected() = runTest {
        val client = UsbObdClient()

        assertFalse(client.isConnected)
        val rpm = client.readRpm()
        val dtcs = client.readDtcs()
        assertTrue(rpm.isFailure)
        assertEquals("USB OBD adapter is not connected", rpm.exceptionOrNull()?.message)
        assertTrue(dtcs.isFailure)
        assertEquals("USB OBD adapter is not connected", dtcs.exceptionOrNull()?.message)
        client.close()
        assertFalse(client.isConnected)
    }
}
