package com.aicarscaner.mobile.data.api

import com.google.gson.annotations.SerializedName
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

data class VehicleCatalogEntryDto(
    val make: String,
    val model: String,
    val chassis: String? = null,
    val year: Int,
    val engine: String,
    val ecu: String? = null,
    val fuel: List<String> = emptyList(),
    val source: String = "",
    val scope: String = ""
)

/** Backend-defined catalogue/engine family hint. Not a verified VIN fitment. */
data class GlobalVehicleModelDto(
    val make: String,
    val model: String,
    @SerializedName("year_ranges") val yearRanges: List<List<Int>> = emptyList(),
    @SerializedName("engine_families") val engineFamilies: List<String> = emptyList(),
    @SerializedName("common_fuels") val commonFuels: List<String> = emptyList(),
    @SerializedName("engine_scope") val engineScope: String = "family-level",
    val source: String = "",
    val disclaimer: String = ""
)

data class GlobalVehiclePhotoDto(
    val status: String,
    @SerializedName("image_url") val imageUrl: String? = null,
    @SerializedName("fallback_generated_portrait") val fallbackPortrait: String? = null,
    @SerializedName("file_page") val filePage: String? = null,
    val title: String? = null,
    val author: String? = null,
    val license: String? = null,
    val notice: String? = null
)

data class ObdProtocolHintDto(
    val id: String,
    val standard: String,
    val support: String
)

data class ObdCompatibilityDto(
    val year: Int,
    val market: String,
    val candidates: List<ObdProtocolHintDto>,
    val confidence: String,
    val warnings: List<String>,
    val notice: String
)

data class VehicleDto(
    val make: String,
    val model: String,
    val chassis: String? = null,
    val year: Int? = null,
    val engine: String? = null,
    val fuel: List<String> = emptyList(),
    val ecu: String? = null
)
data class SymptomRequest(
    val raw_text: String,
    val normalized: Map<String, String> = emptyMap(),
    val symptom: String? = null
)
data class DtcRequest(val code: String, val description: String? = null)

data class DtcDto(
    val id: String? = null,
    val code: String,
    val description: String? = null,
    val source: String? = null
)

data class SymptomDto(
    val id: String,
    val raw_text: String,
    val normalized: Map<String, String> = emptyMap()
)

data class EvidenceDto(
    val id: String,
    val fact: String,
    val source: String,
    val status: String,
    val confidence: Double? = null
)

data class HypothesisDto(
    val id: String,
    val category: String,
    val statement: String,
    val supporting_evidence_ids: List<String> = emptyList(),
    val contradicting_evidence_ids: List<String> = emptyList(),
    val status: String
)

data class RecommendationDto(
    val id: String,
    @SerializedName("name")
    val title: String,
    val purpose: String,
    @SerializedName("priority_score")
    val priority: Double,
    val expected_observation: String? = null,
    @SerializedName("expected_information_gain")
    val informationGain: Double = 0.0,
    @SerializedName("estimated_cost")
    val estimatedCost: Double = 0.0,
    @SerializedName("risk_level")
    val riskLevel: String = "LOW",
    val prerequisites: List<String> = emptyList(),
    val target_hypotheses: List<String> = emptyList(),
    val safety_notes: List<String> = emptyList()
)

data class TestResultRequest(
    val test_id: String,
    val result: String,
    val measurements: Map<String, Any?> = emptyMap(),
    val notes: String? = null
)

data class TestResultDto(
    val test_id: String,
    val result: String,
    val result_label: String? = null,
    val measurements: Map<String, Any?> = emptyMap(),
    val notes: String? = null,
    @SerializedName("test_name") val testName: String? = null
)

data class AuditEventDto(
    val event: String,
    val hypotheses: Int? = null,
    val evidence_count: Int? = null,
    val hypothesis_count: Int? = null,
    val questions: List<String>? = null
)

data class DiagnosticSessionDto(
    val session_id: String,
    val state: String,
    val vehicle: VehicleDto? = null,
    val symptoms: List<SymptomDto> = emptyList(),
    val dtcs: List<DtcDto> = emptyList(),
    val evidence: List<EvidenceDto> = emptyList(),
    val hypotheses: List<HypothesisDto> = emptyList(),
    val recommendations: List<RecommendationDto> = emptyList(),
    val test_results: List<TestResultDto> = emptyList(),
    val audit_log: List<AuditEventDto> = emptyList()
)

data class BackendLiveRecordDto(
    val channel: String? = null,
    val pid: String? = null,
    val numeric_value: Double? = null,
    val unit: String? = null,
    val source_type: String? = null,
    val metadata: Map<String, String>? = null
)

data class BackendLiveRecordsDto(val records: List<BackendLiveRecordDto> = emptyList())

interface DiagnosticApi {
    @GET("api/v1/acquisition/sessions/{sessionId}/records")
    suspend fun acquisitionRecords(
        @Path("sessionId") sessionId: String,
        @Query("limit") limit: Int = 100
    ): BackendLiveRecordsDto

    @GET("api/v1/obd/plan")
    suspend fun obdPlan(): ObdPlanDto

    @POST("api/v1/obd/decode")
    suspend fun decodeObd(@Body frames: ObdRawSnapshotDto): ObdDecodedSnapshotDto

    @GET("api/v1/sessions")
    suspend fun listSessions(): List<DiagnosticSessionDto>

    @GET("api/v1/sessions/{sessionId}")
    suspend fun getSession(@Path("sessionId") sessionId: String, @Query("language") language: String = "en"): DiagnosticSessionDto

    @GET("api/v1/vehicle-catalog/entries")
    suspend fun vehicleCatalog(): List<VehicleCatalogEntryDto>

    // Global models, engine families and protocol candidates come from Backend.
    @GET("api/v1/vehicle-registry/makes")
    suspend fun vehicleRegistryMakes(): List<String>

    @GET("api/v1/vehicle-registry/models")
    suspend fun vehicleRegistryModels(
        @Query("make") make: String,
        @Query("year") year: Int? = null
    ): List<GlobalVehicleModelDto>

    @GET("api/v1/vehicle-registry/compatibility")
    suspend fun vehicleProtocolHints(
        @Query("year") year: Int,
        @Query("market") market: String = "unknown",
        @Query("make") make: String = ""
    ): ObdCompatibilityDto

    @GET("api/v1/vehicle-registry/photo")
    suspend fun vehicleImageMetadata(
        @Query("make") make: String,
        @Query("model") model: String,
        @Query("chassis") chassis: String = ""
    ): GlobalVehiclePhotoDto

    @POST("api/v1/sessions")
    suspend fun createSession(@Body vehicle: VehicleDto): DiagnosticSessionDto

    @PUT("api/v1/sessions/{sessionId}/vehicle")
    suspend fun updateVehicle(
        @Path("sessionId") sessionId: String,
        @Body vehicle: VehicleDto
    ): DiagnosticSessionDto

    @POST("api/v1/sessions/{sessionId}/symptoms")
    suspend fun addSymptom(@Path("sessionId") sessionId: String, @Body request: SymptomRequest): DiagnosticSessionDto

    @PUT("api/v1/sessions/{sessionId}/symptoms/{symptomId}")
    suspend fun updateSymptom(
        @Path("sessionId") sessionId: String,
        @Path("symptomId") symptomId: String,
        @Body request: SymptomRequest
    ): DiagnosticSessionDto

    @DELETE("api/v1/sessions/{sessionId}/symptoms/{symptomId}")
    suspend fun deleteSymptom(
        @Path("sessionId") sessionId: String,
        @Path("symptomId") symptomId: String
    ): DiagnosticSessionDto

    @POST("api/v1/sessions/{sessionId}/dtcs")
    suspend fun addDtc(@Path("sessionId") sessionId: String, @Body request: DtcRequest): DiagnosticSessionDto

    @PUT("api/v1/sessions/{sessionId}/dtcs/{dtcId}")
    suspend fun updateDtc(
        @Path("sessionId") sessionId: String,
        @Path("dtcId") dtcId: String,
        @Body request: DtcRequest
    ): DiagnosticSessionDto

    @DELETE("api/v1/sessions/{sessionId}/dtcs/{dtcId}")
    suspend fun deleteDtc(
        @Path("sessionId") sessionId: String,
        @Path("dtcId") dtcId: String
    ): DiagnosticSessionDto

    @POST("api/v1/intelligence/sessions/{sessionId}/test-results")
    suspend fun recordTestResult(
        @Path("sessionId") sessionId: String,
        @Body request: TestResultRequest,
        @Query("language") language: String = "en"
    ): DiagnosticSessionDto

    @POST("api/v1/analysis/{sessionId}")
    suspend fun analyze(
        @Path("sessionId") sessionId: String,
        @Query("language") language: String = "en"
    ): DiagnosticSessionDto
}


data class ObdPlanDto(val initialization: List<String>, val commands: List<String>)
data class ObdRawSnapshotDto(val responses: Map<String, String>, val session_id: String? = null)
data class ObdDecodedSnapshotDto(val values: com.aicarscaner.mobile.data.obd.LiveDataSnapshot)
