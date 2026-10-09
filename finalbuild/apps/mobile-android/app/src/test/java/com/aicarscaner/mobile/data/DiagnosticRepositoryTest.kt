package com.aicarscaner.mobile.data

import com.aicarscaner.mobile.data.api.DiagnosticApi
import com.aicarscaner.mobile.data.api.DiagnosticSessionDto
import com.aicarscaner.mobile.data.api.DtcRequest
import com.aicarscaner.mobile.data.api.SymptomRequest
import com.aicarscaner.mobile.data.api.VehicleDto
import com.aicarscaner.mobile.data.repository.DiagnosticRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Test

class DiagnosticRepositoryTest {
    private val api = mockk<DiagnosticApi>()
    private val repository = DiagnosticRepository(api)
    private val session = DiagnosticSessionDto(session_id = "session-1", state = "COLLECTING")

    @Test
    fun addSymptomTrimsInputAndSendsNormalizedText() = runTest {
        coEvery { api.addSymptom("session-1", any<SymptomRequest>()) } returns session

        assertEquals(session, repository.addSymptom("session-1", "  rough idle  "))

        coVerify {
            api.addSymptom("session-1", match {
                it.raw_text == "rough idle" && it.symptom == "rough idle"
            })
        }
    }

    @Test
    fun addDtcTrimsAndUppercasesCode() = runTest {
        coEvery { api.addDtc("session-1", any<DtcRequest>()) } returns session

        assertEquals(session, repository.addDtc("session-1", " p0302 "))

        coVerify { api.addDtc("session-1", match { it.code == "P0302" }) }
    }

    @Test
    fun updateVehiclePassesSessionAndVehicleToApi() = runTest {
        val vehicle = VehicleDto(make = "Mercedes-Benz", model = "E350", year = 2006, engine = "M272")
        coEvery { api.updateVehicle("session-1", vehicle) } returns session

        assertEquals(session, repository.updateVehicle("session-1", vehicle))

        coVerify(exactly = 1) { api.updateVehicle("session-1", vehicle) }
    }

    @Test
    fun analyzePassesRequestedLanguage() = runTest {
        coEvery { api.analyze("session-1", "hy") } returns session

        assertEquals(session, repository.analyze("session-1", "hy"))

        coVerify(exactly = 1) { api.analyze("session-1", "hy") }
    }
}
