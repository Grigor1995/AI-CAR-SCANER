package com.aicarscaner.mobile.data.obd

import com.aicarscaner.mobile.data.api.ObdPlanDto
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.test.runTest
import org.junit.Assert.*
import org.junit.Test
import java.io.IOException

class LivePollingSessionTest {
    private val bootstrap=ObdPlanDto(emptyList(),listOf("010C","010D"),listOf("0100","ATDPN"))

    @Test fun backendSelectsCommandsAndCapabilitiesAreQueriedOnlyOncePerConnection() = runTest {
        var loads=0;var selections=0
        val commands=mutableListOf<String>()
        val poller=LivePollingSession(loadPlan={loads++;bootstrap},negotiate={
            selections++
            assertEquals(mapOf("0100" to "raw-0100", "ATDPN" to "raw-ATDPN"),it)
            ObdPlanDto(emptyList(),listOf("010D"))
        },decodeFrames={frames,session ->
            assertEquals("session-1",session)
            assertEquals(setOf("0100","ATDPN","010D"),frames.keys)
            LiveDataSnapshot(speedKph=42.0)
        })
        repeat(2) {
            assertEquals(42.0,poller.read("session-1") {commands+=it;Result.success("raw-$it")}.getOrThrow().speedKph!!,0.001)
        }
        assertEquals(1,loads);assertEquals(1,selections)
        assertEquals(listOf("0100","ATDPN","010D","010D"),commands)
    }

    @Test fun malformedCapabilityRejectionNeverFallsBackToLiveCommands() = runTest {
        val commands=mutableListOf<String>();var decoded=false
        val poller=LivePollingSession(loadPlan={bootstrap},negotiate={throw IOException("HTTP 422 invalid bitmap")},
            decodeFrames={_,_->decoded=true;LiveDataSnapshot()})
        assertTrue(poller.read(null) {commands+=it;Result.success("NO DATA")}.isFailure)
        assertEquals(listOf("0100","ATDPN"),commands)
        assertFalse(decoded)
    }

    @Test fun emptySupportedPlanDoesNotStartAnEmptyLiveStream() = runTest {
        var decoded=false
        val poller=LivePollingSession(loadPlan={bootstrap},negotiate={ObdPlanDto(emptyList(),emptyList())},
            decodeFrames={_,_->decoded=true;LiveDataSnapshot()})
        assertTrue(poller.read(null) {Result.success("raw")}.exceptionOrNull()!!.message!!.contains("no supported"))
        assertFalse(decoded)
    }

    @Test fun failedPollInvalidatesCapabilitiesBeforeRetry() = runTest {
        var selections=0;val commands=mutableListOf<String>()
        val poller=LivePollingSession(loadPlan={bootstrap},negotiate={selections++;ObdPlanDto(emptyList(),listOf("010C"))},
            decodeFrames={_,_->LiveDataSnapshot(rpm=800.0)})
        assertTrue(poller.read(null) {commands+=it;if(it=="010C") Result.failure(IOException("disconnected")) else Result.success("raw")}.isFailure)
        assertTrue(poller.read(null) {commands+=it;Result.success("raw")}.isSuccess)
        assertEquals(2,selections)
        assertEquals(2,commands.count {it=="0100"})
    }

    @Test fun cancellingCapabilityDiscoveryDoesNotDecodeOrSwallowCancellation() = runTest {
        var selected=false
        val poller=LivePollingSession(loadPlan={bootstrap},negotiate={selected=true;ObdPlanDto(emptyList(),listOf("010C"))})
        try {
            poller.read(null) {Result.failure(CancellationException("stop"))}
            fail("Cancellation must propagate")
        } catch(_:CancellationException) {}
        assertFalse(selected)
    }
}
