package com.aicarscaner.mobile.data.api

import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path

data class CreateSessionRequest(val vehicle: VehicleDto? = null)
data class VehicleDto(
    val make: String,
    val model: String,
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

data class SymptomDto(
    val raw_text: String,
    val normalized: Map<String, String> = emptyMap()
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
    val title: String,
    val purpose: String,
    val priority: Int,
    val expected_observation: String? = null
)

data class AuditEventDto(
    val event: String,
    val hypotheses: Int? = null
)

data class DiagnosticSessionDto(
    val session_id: String,
    val state: String,
    val symptoms: List<SymptomDto> = emptyList(),
    val hypotheses: List<HypothesisDto> = emptyList(),
    val recommendations: List<RecommendationDto> = emptyList(),
    val audit_log: List<AuditEventDto> = emptyList()
)

interface DiagnosticApi {
    @POST("api/v1/sessions")
    suspend fun createSession(@Body vehicle: VehicleDto): DiagnosticSessionDto

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

    @POST("api/v1/analysis/{sessionId}")
    suspend fun analyze(@Path("sessionId") sessionId: String): DiagnosticSessionDto
}
