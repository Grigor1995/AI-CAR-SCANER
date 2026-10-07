package com.aicarscaner.mobile.data.repository

import com.aicarscaner.mobile.data.api.*

class DiagnosticRepository(private val api: DiagnosticApi) {
    suspend fun createSession(vehicle: VehicleDto) =
        api.createSession(vehicle)

    suspend fun addSymptom(sessionId: String, symptom: String) =
        api.addSymptom(sessionId, SymptomRequest(raw_text = symptom.trim(), symptom = symptom.trim()))

    suspend fun addDtc(sessionId: String, code: String) =
        api.addDtc(sessionId, DtcRequest(code))

    suspend fun analyze(sessionId: String) =
        api.analyze(sessionId)
}
