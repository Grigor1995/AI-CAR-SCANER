package com.aicarscaner.mobile.data.api

import com.google.gson.Gson
import kotlinx.coroutines.test.runTest
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class DiagnosticApiContractTest {
    private lateinit var server: MockWebServer
    private lateinit var api: DiagnosticApi

    @Before
    fun setUp() {
        server = MockWebServer()
        server.start()
        api = Retrofit.Builder()
            .baseUrl(server.url("/"))
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(DiagnosticApi::class.java)
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    private fun enqueueSession() {
        server.enqueue(
            MockResponse()
                .setHeader("Content-Type", "application/json")
                .setBody("""{"session_id":"session-1","state":"COLLECTING"}""")
        )
    }

    @Test
    fun vehicleCatalogUsesExpectedEndpointAndParsesEntries() = runTest {
        server.enqueue(
            MockResponse()
                .setHeader("Content-Type", "application/json")
                .setBody("""[{"make":"Mercedes-Benz","model":"E-Class","year":2006,"engine":"M272","fuel":["petrol","lpg"]}]""")
        )

        val entries = api.vehicleCatalog()
        val request = server.takeRequest()

        assertEquals("GET", request.method)
        assertEquals("/api/v1/vehicle-catalog/entries", request.path)
        assertEquals("Mercedes-Benz", entries.single().make)
        assertEquals(listOf("petrol", "lpg"), entries.single().fuel)
    }

    @Test
    fun createSessionSerializesVehiclePayload() = runTest {
        enqueueSession()
        api.createSession(VehicleDto(make = "Mercedes-Benz", model = "E350", year = 2006, engine = "M272"))

        val request = server.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/api/v1/sessions", request.path)
        val body = Gson().fromJson(request.body.readUtf8(), Map::class.java)
        assertEquals("Mercedes-Benz", body["make"])
        assertEquals("E350", body["model"])
        assertEquals(2006.0, body["year"])
    }

    @Test
    fun updateVehicleUsesSessionPathAndPut() = runTest {
        enqueueSession()
        api.updateVehicle("session-1", VehicleDto(make = "Mercedes-Benz", model = "E350"))

        val request = server.takeRequest()
        assertEquals("PUT", request.method)
        assertEquals("/api/v1/sessions/session-1/vehicle", request.path)
    }

    @Test
    fun addSymptomSendsRawTextAndNormalizedSymptom() = runTest {
        enqueueSession()
        api.addSymptom("session-1", SymptomRequest(raw_text = "rough idle", symptom = "rough idle"))

        val request = server.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/api/v1/sessions/session-1/symptoms", request.path)
        val body = Gson().fromJson(request.body.readUtf8(), Map::class.java)
        assertEquals("rough idle", body["raw_text"])
        assertEquals("rough idle", body["symptom"])
    }

    @Test
    fun updateAndDeleteSymptomUseCorrectMethodsAndIds() = runTest {
        enqueueSession()
        api.updateSymptom("session-1", "symptom-7", SymptomRequest(raw_text = "stall"))
        val update = server.takeRequest()
        assertEquals("PUT", update.method)
        assertEquals("/api/v1/sessions/session-1/symptoms/symptom-7", update.path)

        enqueueSession()
        api.deleteSymptom("session-1", "symptom-7")
        val delete = server.takeRequest()
        assertEquals("DELETE", delete.method)
        assertEquals("/api/v1/sessions/session-1/symptoms/symptom-7", delete.path)
    }

    @Test
    fun addDtcSendsCodeToExpectedEndpoint() = runTest {
        enqueueSession()
        api.addDtc("session-1", DtcRequest(code = "P0302"))

        val request = server.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/api/v1/sessions/session-1/dtcs", request.path)
        assertTrue(request.body.readUtf8().contains("\"code\":\"P0302\""))
    }

    @Test
    fun updateAndDeleteDtcUseCorrectMethodsAndIds() = runTest {
        enqueueSession()
        api.updateDtc("session-1", "dtc-3", DtcRequest(code = "P0302"))
        val update = server.takeRequest()
        assertEquals("PUT", update.method)
        assertEquals("/api/v1/sessions/session-1/dtcs/dtc-3", update.path)

        enqueueSession()
        api.deleteDtc("session-1", "dtc-3")
        val delete = server.takeRequest()
        assertEquals("DELETE", delete.method)
        assertEquals("/api/v1/sessions/session-1/dtcs/dtc-3", delete.path)
    }

    @Test
    fun analyzeIncludesRequestedLanguageQuery() = runTest {
        enqueueSession()
        val session = api.analyze("session-1", "hy")

        val request = server.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/api/v1/analysis/session-1?language=hy", request.path)
        assertEquals("session-1", session.session_id)
    }

    @Test
    fun recordTestResultSerializesResultAndLanguage() = runTest {
        enqueueSession()
        api.recordTestResult(
            "session-1",
            TestResultRequest(test_id = "fuel-pressure", result = "FAIL", notes = "pressure low"),
            "ru"
        )

        val request = server.takeRequest()
        assertEquals("POST", request.method)
        assertEquals("/api/v1/intelligence/sessions/session-1/test-results?language=ru", request.path)
        val body = Gson().fromJson(request.body.readUtf8(), Map::class.java)
        assertEquals("fuel-pressure", body["test_id"])
        assertEquals("FAIL", body["result"])
        assertEquals("pressure low", body["notes"])
    }

    @Test
    fun createSessionSurfacesServiceUnavailableAsHttpException() = runTest {
        server.enqueue(
            MockResponse()
                .setResponseCode(503)
                .setHeader("Content-Type", "application/json")
                .setBody("""{"detail":"diagnostic service unavailable"}""")
        )

        val error = runCatching {
            api.createSession(VehicleDto(make = "Mercedes-Benz", model = "E350"))
        }.exceptionOrNull()

        assertTrue("Expected an HTTP exception but got $error", error is retrofit2.HttpException)
        assertEquals(503, (error as retrofit2.HttpException).code())
        assertEquals("/api/v1/sessions", server.takeRequest().path)
    }

    @Test
    fun vehicleCatalogMalformedJsonReturnsDeserializationFailure() = runTest {
        server.enqueue(
            MockResponse()
                .setHeader("Content-Type", "application/json")
                .setBody("""{"not":"a list"}""")
        )

        val result = runCatching { api.vehicleCatalog() }

        assertTrue("Malformed catalog JSON should fail instead of returning entries", result.isFailure)
        assertTrue(
            "Expected a JSON/conversion error, got ${result.exceptionOrNull()}",
            result.exceptionOrNull() is com.google.gson.JsonParseException ||
                result.exceptionOrNull() is java.io.IOException
        )
        assertEquals("/api/v1/vehicle-catalog/entries", server.takeRequest().path)
    }

    @Test
    fun recommendationDtoMapsBackendJsonNames() {
        val recommendation = Gson().fromJson(
            """{"id":"r1","name":"Check fuel pressure","purpose":"validate fuel delivery","priority_score":0.8,"expected_information_gain":0.6,"estimated_cost":25.0,"risk_level":"LOW"}""",
            RecommendationDto::class.java
        )

        assertEquals("Check fuel pressure", recommendation.title)
        assertEquals(0.8, recommendation.priority, 0.0001)
        assertEquals(0.6, recommendation.informationGain, 0.0001)
        assertEquals(25.0, recommendation.estimatedCost, 0.0001)
    }
}
