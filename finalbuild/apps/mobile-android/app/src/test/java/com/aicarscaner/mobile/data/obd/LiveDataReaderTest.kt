package com.aicarscaner.mobile.data.obd

import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.IOException

class LiveDataReaderTest {
    @Test
    fun parsesSupportedPidsAndAppliesObdScalingFormulas() = runTest {
        val responses = mapOf(
            "010C" to "SEARCHING...410C1AF8",
            "010D" to "410D32",
            "0105" to "41057B",
            "0104" to "410480",
            "010F" to "410F50",
            "0110" to "411001F4",
            "010B" to "410B64",
            "0111" to "411180",
            "0106" to "410680",
            "0107" to "4107A0"
        )

        val result = LiveDataReader.read { command ->
            Result.success(responses.getValue(command))
        }

        assertTrue(result.isSuccess)
        val snapshot = result.getOrThrow()
        assertEquals(1726.0, snapshot.rpm!!, 0.0001)
        assertEquals(50.0, snapshot.speedKph!!, 0.0001)
        assertEquals(83.0, snapshot.coolantC!!, 0.0001)
        assertEquals(128.0 * 100.0 / 255.0, snapshot.engineLoadPct!!, 0.0001)
        assertEquals(40.0, snapshot.intakeAirC!!, 0.0001)
        assertEquals(5.0, snapshot.mafGps!!, 0.0001)
        assertEquals(100.0, snapshot.mapKpa!!, 0.0001)
        assertEquals(128.0 * 100.0 / 255.0, snapshot.throttlePct!!, 0.0001)
        assertEquals(0.0, snapshot.shortFuelTrimPct!!, 0.0001)
        assertEquals(25.0, snapshot.longFuelTrimPct!!, 0.0001)
    }

    @Test
    fun unsupportedAndMalformedPidResponsesBecomeNullValues() = runTest {
        val responses = mapOf(
            "010C" to "NO DATA",
            "010D" to "ERROR",
            "0105" to "UNABLE TO CONNECT",
            "0104" to "4104",
            "010F" to "410F",
            "0110" to "411001",
            "010B" to "420B64",
            "0111" to "4111GG",
            "0106" to "4106GG",
            "0107" to "4107"
        )

        val snapshot = LiveDataReader.read { command ->
            Result.success(responses.getValue(command))
        }.getOrThrow()

        assertNull(snapshot.rpm)
        assertNull(snapshot.speedKph)
        assertNull(snapshot.coolantC)
        assertNull(snapshot.engineLoadPct)
        assertNull(snapshot.intakeAirC)
        assertNull(snapshot.mafGps)
        assertNull(snapshot.mapKpa)
        assertNull(snapshot.throttlePct)
        assertNull(snapshot.shortFuelTrimPct)
        assertNull(snapshot.longFuelTrimPct)
    }

    @Test
    fun trimsWhitespaceAndParsesLowercasePidResponse() = runTest {
        val snapshot = LiveDataReader.read { command ->
            if (command == "010C") Result.success("  410c 1af8  ")
            else Result.success("NO DATA")
        }.getOrThrow()

        assertEquals(1726.0, snapshot.rpm!!, 0.0001)
    }

    @Test
    fun individualCommandFailureDoesNotDiscardOtherLiveData() = runTest {
        val snapshot = LiveDataReader.read { command ->
            if (command == "010C") Result.failure(IOException("adapter read failed"))
            else if (command == "010D") Result.success("410D28")
            else Result.success("NO DATA")
        }.getOrThrow()

        assertNull(snapshot.rpm)
        assertEquals(40.0, snapshot.speedKph!!, 0.0001)
    }

    @Test
    fun thrownCommandExceptionIsReturnedAsFailure() = runTest {
        val result = LiveDataReader.read { throw IOException("adapter disconnected") }

        assertFalse(result.isSuccess)
        assertTrue(result.exceptionOrNull() is IOException)
        assertEquals("adapter disconnected", result.exceptionOrNull()?.message)
    }
}
