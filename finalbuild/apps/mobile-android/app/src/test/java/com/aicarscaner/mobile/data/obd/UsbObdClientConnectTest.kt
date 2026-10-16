package com.aicarscaner.mobile.data.obd

import android.hardware.usb.UsbConstants
import android.hardware.usb.UsbDevice
import android.hardware.usb.UsbDeviceConnection
import android.hardware.usb.UsbEndpoint
import android.hardware.usb.UsbInterface
import android.hardware.usb.UsbManager
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class UsbObdClientConnectTest {
    @Test
    fun permissionDeniedReturnsReadableFailure() = runTest {
        val manager = mockk<UsbManager>()
        val device = mockk<UsbDevice>()
        every { manager.hasPermission(device) } returns false
        every { device.deviceName } returns "usb-test-device"

        val client = UsbObdClient()
        val result = client.connect(manager, device)

        assertTrue(result.isFailure)
        assertEquals(
            "USB permission is required for usb-test-device",
            result.exceptionOrNull()?.message
        )
        assertFalse(client.isConnected)
    }

    @Test
    fun deviceWithoutBulkInterfaceReturnsReadableFailure() = runTest {
        val manager = mockk<UsbManager>()
        val device = mockk<UsbDevice>()
        val intf = mockk<UsbInterface>()
        val endpoint = mockk<UsbEndpoint>()
        every { manager.hasPermission(device) } returns true
        every { device.deviceName } returns "usb-test-device"
        every { device.interfaceCount } returns 1
        every { device.getInterface(0) } returns intf
        every { intf.endpointCount } returns 1
        every { intf.getEndpoint(0) } returns endpoint
        every { endpoint.type } returns UsbConstants.USB_ENDPOINT_XFER_INT

        val client = UsbObdClient()
        val result = client.connect(manager, device)

        assertTrue(result.isFailure)
        assertEquals(
            "No bulk USB serial interface found on usb-test-device",
            result.exceptionOrNull()?.message
        )
        assertFalse(client.isConnected)
    }

    @Test
    fun failedOpenReturnsFailureAndLeavesClientDisconnected() = runTest {
        val manager = mockk<UsbManager>()
        val (device, intf, _, _) = bulkDevice()
        every { manager.hasPermission(device) } returns true
        every { manager.openDevice(device) } returns null
        every { device.deviceName } returns "usb-test-device"

        val client = UsbObdClient()
        val result = client.connect(manager, device)

        assertTrue(result.isFailure)
        assertEquals(
            "Unable to open USB device usb-test-device",
            result.exceptionOrNull()?.message
        )
        assertFalse(client.isConnected)
    }

    @Test
    fun failedInterfaceClaimClosesOpenedDeviceConnection() = runTest {
        val manager = mockk<UsbManager>()
        val (device, intf, _, _) = bulkDevice()
        val handle = mockk<UsbDeviceConnection>()
        every { manager.hasPermission(device) } returns true
        every { manager.openDevice(device) } returns handle
        every { handle.claimInterface(intf, true) } returns false
        every { handle.releaseInterface(intf) } returns false
        every { handle.close() } returns Unit

        val client = UsbObdClient()
        val result = client.connect(manager, device)

        assertTrue(result.isFailure)
        assertEquals("Unable to claim USB interface", result.exceptionOrNull()?.message)
        assertFalse(client.isConnected)
        verify(exactly = 1) { handle.close() }
    }

    @Test
    fun successfulUsbConnectionInitializesAdapterAndReadsResponses() = runTest {
        val manager = mockk<UsbManager>()
        val (device, intf, input, output) = bulkDevice()
        val handle = mockk<UsbDeviceConnection>()
        val sentCommands = mutableListOf<String>()
        val responses = ArrayDeque(
            listOf("OK\r>", "OK\r>", "OK\r>", "OK\r>", "OK\r>",
                "SEARCHING...\r410C1AF8\r>", "430102\r>")
        )

        every { manager.hasPermission(device) } returns true
        every { manager.openDevice(device) } returns handle
        every { device.productName } returns "USB ELM327"
        every { handle.claimInterface(intf, true) } returns true
        every { handle.releaseInterface(intf) } returns true
        every { handle.close() } returns Unit
        every { handle.bulkTransfer(output, any<ByteArray>(), any(), any()) } answers {
            val bytes = secondArg<ByteArray>()
            val length = thirdArg<Int>()
            sentCommands.add(String(bytes, 0, length, Charsets.US_ASCII))
            length
        }
        every { handle.bulkTransfer(input, any<ByteArray>(), any(), any()) } answers {
            val buffer = secondArg<ByteArray>()
            val bytes = responses.removeFirst().toByteArray(Charsets.US_ASCII)
            bytes.copyInto(buffer)
            bytes.size
        }

        val client = UsbObdClient()
        val connected = client.connect(manager, device)

        assertTrue(connected.isSuccess)
        assertEquals("Connected to USB USB ELM327", connected.getOrThrow())
        assertTrue(client.isConnected)
        assertEquals("410C1AF8", client.readRpm().getOrThrow())
        assertEquals("430102", client.readDtcs().getOrThrow())
        assertEquals(
            listOf("ATZ\r", "ATE0\r", "ATL0\r", "ATS0\r", "ATSP0\r", "010C\r", "03\r"),
            sentCommands
        )

        client.close()
        assertFalse(client.isConnected)
        verify(exactly = 1) { handle.releaseInterface(intf) }
        verify(exactly = 1) { handle.close() }
    }

    private fun bulkDevice(): Quadruple<UsbDevice, UsbInterface, UsbEndpoint, UsbEndpoint> {
        val device = mockk<UsbDevice>()
        val intf = mockk<UsbInterface>()
        val input = mockk<UsbEndpoint>()
        val output = mockk<UsbEndpoint>()
        every { device.deviceName } returns "usb-test-device"
        every { device.interfaceCount } returns 1
        every { device.getInterface(0) } returns intf
        every { intf.endpointCount } returns 2
        every { intf.getEndpoint(0) } returns input
        every { intf.getEndpoint(1) } returns output
        every { input.type } returns UsbConstants.USB_ENDPOINT_XFER_BULK
        every { input.direction } returns UsbConstants.USB_DIR_IN
        every { output.type } returns UsbConstants.USB_ENDPOINT_XFER_BULK
        every { output.direction } returns UsbConstants.USB_DIR_OUT
        return Quadruple(device, intf, input, output)
    }

    private data class Quadruple<A, B, C, D>(
        val first: A,
        val second: B,
        val third: C,
        val fourth: D
    )
}
