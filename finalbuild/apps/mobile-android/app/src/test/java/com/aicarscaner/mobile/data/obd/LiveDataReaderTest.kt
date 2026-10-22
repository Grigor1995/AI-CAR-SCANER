package com.aicarscaner.mobile.data.obd

import com.aicarscaner.mobile.data.api.ObdPlanDto
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Test
import java.io.IOException

/** PID formulas are covered by the shared backend suite; this tests bridge IO. */
class LiveDataReaderTest {
    private val plan = ObdPlanDto(emptyList(), listOf("010C", "010D"))

    @Test fun forwardsRawFramesAndUsesBackendValuesWithoutLocalScaling() = runTest {
        var captured = emptyMap<String, String>()
        val result = LiveDataReader.read(plan = { plan }, decode = {
            captured = it; LiveDataSnapshot(rpm = 1234.5, speedKph = 42.0)
        }) { Result.success("arbitrary raw frame") }.getOrThrow()
        assertEquals(mapOf("010C" to "arbitrary raw frame", "010D" to "arbitrary raw frame"), captured)
        assertEquals(1234.5, result.rpm!!, 0.001)
        assertEquals(42.0, result.speedKph!!, 0.001)
    }

    @Test fun failedIndividualReadIsForwardedAsMissingData() = runTest {
        var captured = emptyMap<String, String>()
        LiveDataReader.read(plan = { plan }, decode = { captured = it; LiveDataSnapshot() }) {
            if (it == "010C") Result.failure(IOException("timeout")) else Result.success("410D28")
        }.getOrThrow()
        assertEquals("NO DATA", captured["010C"])
        assertEquals("410D28", captured["010D"])
    }

    @Test fun backendFailureIsNotReportedAsSuccessfulDiagnosis() = runTest {
        val result = LiveDataReader.read(plan = { plan }, decode = { throw IOException("backend offline") }) { Result.success("410C0000") }
        assertEquals("backend offline", result.exceptionOrNull()?.message)
    }

    @Test fun failedPlanDoesNotSendCommands() = runTest {
        var commands = 0
        val result = LiveDataReader.read(plan = { throw IOException("plan unavailable") }, decode = { LiveDataSnapshot() }) { commands++; Result.success("OK") }
        assertTrue(result.isFailure)
        assertEquals(0, commands)
    }

    @Test fun cancellationPropagatesToStopPolling() = runTest {
        try {
            LiveDataReader.read(plan = { throw CancellationException("stop") }, decode = { LiveDataSnapshot() }) { Result.success("OK") }
            fail("Cancellation must propagate")
        } catch (_: CancellationException) { }
    }
}
