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

data class CreateSessionRequest(val vehicle: VehicleDto? = null)
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

interface DiagnosticApi {
    @GET("api/v1/sessions")
    suspend fun listSessions(): List<DiagnosticSessionDto>

    @GET("api/v1/sessions/{sessionId}")
    suspend fun getSession(@Path("sessionId") sessionId: String): DiagnosticSessionDto

    @GET("api/v1/vehicle-catalog/entries")
    suspend fun vehicleCatalog(): List<VehicleCatalogEntryDto>

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
