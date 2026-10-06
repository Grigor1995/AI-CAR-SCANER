package com.aicarscaner.mobile.data.api

import retrofit2.http.Body
import retrofit2.http.POST
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
data class SymptomRequest(val raw_text: String)
data class DtcRequest(val code: String, val description: String? = null)
data class DiagnosticSessionDto(val session_id: String, val state: String)

interface DiagnosticApi {
    @POST("api/v1/sessions")
    suspend fun createSession(@Body vehicle: VehicleDto): DiagnosticSessionDto

    @POST("api/v1/sessions/{sessionId}/symptoms")
    suspend fun addSymptom(@Path("sessionId") sessionId: String, @Body request: SymptomRequest): DiagnosticSessionDto

    @POST("api/v1/sessions/{sessionId}/dtcs")
    suspend fun addDtc(@Path("sessionId") sessionId: String, @Body request: DtcRequest): DiagnosticSessionDto

    @POST("api/v1/sessions/{sessionId}/analyze")
    suspend fun analyze(@Path("sessionId") sessionId: String): DiagnosticSessionDto
}
