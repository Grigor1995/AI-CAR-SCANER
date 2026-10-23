package com.aicarscaner.mobile.data.obd

import com.aicarscaner.mobile.data.api.*
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.withContext

/** Native transport only; the backend supplies commands and interprets every reply. */
internal object DiscoveryReader {
    suspend fun read(
        plan: suspend () -> DiscoveryPlanDto = { ApiClient.diagnosticApi.discoveryPlan() },
        decode: suspend (ObdRawSnapshotDto) -> DiscoveryResultDto = { ApiClient.diagnosticApi.decodeDiscovery(it) },
        command: suspend (String) -> String
    ): DiscoveryResultDto {
        val steps = plan()
        val responses = linkedMapOf<String,String>()
        try {
            for(step in steps.commands) responses[step] = command(step)
        } finally {
            withContext(NonCancellable) { for(step in steps.restore) command(step) }
        }
        return decode(ObdRawSnapshotDto(responses))
    }
}
