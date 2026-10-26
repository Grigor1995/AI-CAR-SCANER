package com.aicarscaner.mobile.data.obd

data class LiveDataSnapshot(
    val rpm: Double? = null,
    @com.google.gson.annotations.SerializedName("speed_kmh") val speedKph: Double? = null,
    @com.google.gson.annotations.SerializedName("coolant_c") val coolantC: Double? = null,
    @com.google.gson.annotations.SerializedName("engine_load_percent") val engineLoadPct: Double? = null,
    @com.google.gson.annotations.SerializedName("intake_air_c") val intakeAirC: Double? = null,
    @com.google.gson.annotations.SerializedName("maf_gps") val mafGps: Double? = null,
    @com.google.gson.annotations.SerializedName("map_kpa") val mapKpa: Double? = null,
    @com.google.gson.annotations.SerializedName("throttle_percent") val throttlePct: Double? = null,
    @com.google.gson.annotations.SerializedName("short_fuel_trim_percent") val shortFuelTrimPct: Double? = null,
    @com.google.gson.annotations.SerializedName("long_fuel_trim_percent") val longFuelTrimPct: Double? = null,
    val updatedAtMs: Long = System.currentTimeMillis()
)

/** Device IO only. Commands and diagnostic decoding belong to the backend. */
object LiveDataReader {
    suspend fun read(
        sessionId: String? = null,
        plan: suspend () -> com.aicarscaner.mobile.data.api.ObdPlanDto = { com.aicarscaner.mobile.data.api.ApiClient.diagnosticApi.obdPlan() },
        decode: suspend (Map<String, String>) -> LiveDataSnapshot = {
            com.aicarscaner.mobile.data.api.ApiClient.diagnosticApi.decodeObd(
                com.aicarscaner.mobile.data.api.ObdRawSnapshotDto(it, sessionId)
            ).values
        },
        command: suspend (String) -> Result<String>
    ): Result<LiveDataSnapshot> = try {
        // A missing ECU PID is a successful "NO DATA" reply. A transport
        // failure must abort; never turn a disconnected adapter into a snapshot.
        val responses = plan().commands.associateWith { command(it).getOrThrow() }
        Result.success(decode(responses).copy(updatedAtMs = System.currentTimeMillis()))
    } catch (cancelled: kotlinx.coroutines.CancellationException) {
        throw cancelled
    } catch (error: Exception) {
        Result.failure(error)
    }
}
