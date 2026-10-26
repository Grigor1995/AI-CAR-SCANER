package com.aicarscaner.mobile.data.obd

import com.aicarscaner.mobile.data.api.ApiClient
import com.aicarscaner.mobile.data.api.ObdPlanDto
import com.aicarscaner.mobile.data.api.ObdRawSnapshotDto
import kotlinx.coroutines.CancellationException

/** Connection-scoped byte bridge. Only the backend interprets capability masks. */
internal class LivePollingSession(
    private val loadPlan: suspend () -> ObdPlanDto = { ApiClient.diagnosticApi.obdPlan() },
    private val negotiate: suspend (Map<String,String>) -> ObdPlanDto = {
        ApiClient.diagnosticApi.supportedObdPlan(ObdRawSnapshotDto(it))
    },
    private val decodeFrames: suspend (Map<String,String>,String?) -> LiveDataSnapshot = { frames, session ->
        ApiClient.diagnosticApi.decodeObd(ObdRawSnapshotDto(frames,session)).values
    }
) {
    private var activePlan: ObdPlanDto? = null
    private var capabilityFrames: Map<String,String> = emptyMap()

    suspend fun read(sessionId: String?, command: suspend (String) -> Result<String>): Result<LiveDataSnapshot> = try {
        if (activePlan == null) {
            val bootstrap=loadPlan()
            require(bootstrap.discovery.isNotEmpty()) { "Backend capability discovery plan is unavailable" }
            val observed=bootstrap.discovery.associateWith { command(it).getOrThrow() }
            val selected=negotiate(observed)
            require(selected.commands.isNotEmpty()) { "Vehicle reports no supported live channels" }
            capabilityFrames=observed
            activePlan=selected
        }
        LiveDataReader.read(sessionId=sessionId, plan={requireNotNull(activePlan)},
            decode={decodeFrames(capabilityFrames + it,sessionId)}, command=command).getOrThrow().let { Result.success(it) }
    } catch(cancelled: CancellationException) {
        activePlan=null; capabilityFrames=emptyMap()
        throw cancelled
    } catch(error: Exception) {
        activePlan=null; capabilityFrames=emptyMap()
        Result.failure(error)
    }
}
