package com.aicarscaner.mobile.data.api

import kotlinx.coroutines.test.runTest
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.Assert.*
import org.junit.Test
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

class BackendParityContractTest {
    @Test fun simulatorUsesCanonicalSIAndSeparateAcquisitionRoutes() = runTest {
        val server=MockWebServer();server.start()
        try {
            val api=Retrofit.Builder().baseUrl(server.url("/")).addConverterFactory(GsonConverterFactory.create()).build().create(DiagnosticApi::class.java)
            server.enqueue(MockResponse().setBody("{}"))
            api.startAcquisition("case",mapOf("adapter" to "simulator"))
            val start=server.takeRequest();assertEquals("/api/v1/acquisition/sessions/case/start",start.path);assertTrue(start.body.readUtf8().contains("simulator"))
            server.enqueue(MockResponse().setBody("{}"))
            api.simulatorParameters("case",mapOf("rpm" to 1800.0,"coolant_c" to 98.0,"speed_kmh" to 40.0,"throttle_percent" to 32.0))
            val update=server.takeRequest();assertEquals("PUT",update.method);assertTrue(update.path!!.endsWith("/simulator/parameters"));assertTrue(update.body.readUtf8().contains("coolant_c"))
            server.enqueue(MockResponse().setBody("{}"));api.stopAcquisition("case");assertEquals("/api/v1/acquisition/sessions/case/stop",server.takeRequest().path)
            server.enqueue(MockResponse().setBody("{}"));api.analyzeLive("case","hy");assertEquals("/api/v1/telemetry/sessions/case/ai-analyze-live?language=hy",server.takeRequest().path)
        } finally {server.shutdown()}
    }
    @Test fun pdfIsDownloadedAsBytesAndProfilesAreBackendOwned() = runTest {
        val server=MockWebServer();server.start()
        try {
            val api=Retrofit.Builder().baseUrl(server.url("/")).addConverterFactory(GsonConverterFactory.create()).build().create(DiagnosticApi::class.java)
            server.enqueue(MockResponse().setHeader("Content-Type","application/pdf").setBody("%PDF-1.4 demo"))
            assertTrue(api.report("case","pdf","ru").string().startsWith("%PDF-"))
            assertEquals("/api/v1/sessions/case/report?format=pdf&language=ru",server.takeRequest().path)
            val json="""{"id":"profile","name":"Car","vehicle":{"make":"Ford","model":"Mondeo"}}"""
            server.enqueue(MockResponse().setBody(json));val profile=api.saveProfile(VehicleProfileRequest("Car",VehicleDto("Ford","Mondeo")))
            assertEquals("/api/v1/vehicle-profiles",server.takeRequest().path);assertEquals("Ford",profile.vehicle.make)
            server.enqueue(MockResponse().setBody(json));api.updateProfile("profile",VehicleProfileRequest("Car",VehicleDto("Ford","Mondeo")));assertEquals("PUT",server.takeRequest().method)
            server.enqueue(MockResponse().setBody("{}"));api.deleteProfile("profile");val deleted=server.takeRequest();assertEquals("DELETE",deleted.method);assertEquals("/api/v1/vehicle-profiles/profile",deleted.path)
        } finally {server.shutdown()}
    }
}
