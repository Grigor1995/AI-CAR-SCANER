package com.aicarscaner.mobile.data.obd

import com.aicarscaner.mobile.data.api.*
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test

class DiscoveryReaderTest {
    private val plan = DiscoveryPlanDto(listOf("0902","ATH1","0100","ATDPN"),listOf("ATH0"))
    @Test fun vinFirstAndHeadersRestoredBeforeBackendDecode() = runBlocking {
        val seen=mutableListOf<String>()
        val expected=DiscoveryResultDto(null,null,"vin_unavailable",emptyList(),false)
        val result=DiscoveryReader.read(plan={plan},decode={
            assertEquals(plan.commands+plan.restore,seen)
            assertEquals(plan.commands,it.responses.keys.toList())
            expected
        }) { step -> seen.add(step); "NO DATA" }
        assertSame(expected,result)
    }
    @Test fun failedReadStillRestoresAndDoesNotDecode() = runBlocking {
        val seen=mutableListOf<String>()
        try {
            DiscoveryReader.read(plan={plan},decode={error("Must not decode incomplete transaction")}) { step ->
                seen.add(step)
                if(step=="0100") error("Disconnected")
                "OK"
            }
            fail("Expected read error")
        } catch(expected:IllegalStateException) {
            assertEquals(listOf("0902","ATH1","0100","ATH0"),seen)
        }
    }
}
