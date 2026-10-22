package com.aicarscaner.mobile.data.repository

import com.aicarscaner.mobile.data.api.*

class DiagnosticRepository(private val api: DiagnosticApi, private val context: android.content.Context? = null) {

    /** The exact same versioned JSON snapshot as Desktop, copied at build time. */
    fun offlineVehicleCatalog(): List<VehicleCatalogEntryDto> {
        val appContext = context ?: return emptyList()
        return try {
            val json = appContext.assets.open("vehicle_catalog.json").bufferedReader().use { it.readText() }
            val root = com.google.gson.JsonParser.parseString(json).asJsonObject
            root.getAsJsonArray("vehicles").map { item ->
                val row = item.asJsonObject
                fun value(name: String): String = row.get(name)?.takeUnless { it.isJsonNull }?.asString.orEmpty()
                val fuel = value("fuel").split("+", "/", ",").map { it.trim().lowercase() }.filter { it.isNotEmpty() }
                VehicleCatalogEntryDto(
                    make = value("make"), model = value("model"), chassis = value("chassis"),
                    year = row.get("year").asInt, engine = value("engine"),
                    ecu = value("ecu"), fuel = fuel,
                    source = "shared-offline-snapshot", scope = "offline-reference-not-vin-fitment"
                )
            }
        } catch (_: Exception) { emptyList() }
    }

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
