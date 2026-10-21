package com.aicarscaner.mobile.data.repository

import com.aicarscaner.mobile.data.api.*

class DiagnosticRepository(private val api: DiagnosticApi) {
    suspend fun listSessions() = api.listSessions()
    suspend fun getSession(id: String, language: String = "en") = api.getSession(id, language)

    suspend fun vehicleCatalog() = api.vehicleCatalog()

    suspend fun createSession(vehicle: VehicleDto) =
        api.createSession(vehicle)

    suspend fun updateVehicle(sessionId: String, vehicle: VehicleDto) =
        api.updateVehicle(sessionId, vehicle)

    suspend fun addSymptom(sessionId: String, symptom: String) =
        api.addSymptom(sessionId, SymptomRequest(raw_text = symptom.trim(), symptom = symptom.trim()))

    suspend fun updateSymptom(sessionId: String, symptomId: String, symptom: String) =
        api.updateSymptom(
            sessionId,
            symptomId,
            SymptomRequest(raw_text = symptom.trim(), symptom = symptom.trim())
        )

    suspend fun deleteSymptom(sessionId: String, symptomId: String) =
        api.deleteSymptom(sessionId, symptomId)

    suspend fun addDtc(sessionId: String, code: String) =
        api.addDtc(sessionId, DtcRequest(code.trim().uppercase()))

    suspend fun updateDtc(sessionId: String, dtcId: String, code: String) =
        api.updateDtc(sessionId, dtcId, DtcRequest(code.trim().uppercase()))

    suspend fun deleteDtc(sessionId: String, dtcId: String) =
        api.deleteDtc(sessionId, dtcId)

    suspend fun analyze(sessionId: String, language: String = "en") =
        api.analyze(sessionId, language)

    suspend fun recordTestResult(
        sessionId: String,
        testId: String,
        result: String,
        notes: String?,
        language: String = "en"
    ) = api.recordTestResult(
        sessionId,
        TestResultRequest(testId, result, notes = notes),
        language
    )
}
