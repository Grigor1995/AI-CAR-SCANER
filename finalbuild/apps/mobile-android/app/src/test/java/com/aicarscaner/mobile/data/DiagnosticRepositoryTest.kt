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
    fun vehicleCatalogReturnsApiEntries() = runTest {
        val entries = listOf(
            com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto(
                make = "Mercedes-Benz", model = "E-Class", chassis = "W211",
                year = 2006, engine = "M272", fuel = listOf("petrol", "lpg")
            )
        )
        coEvery { api.vehicleCatalog() } returns entries

        assertEquals(entries, repository.vehicleCatalog())
        coVerify(exactly = 1) { api.vehicleCatalog() }
    }

    @Test
    fun createSessionPassesVehiclePayload() = runTest {
        val vehicle = VehicleDto(
            make = "Mercedes-Benz", model = "E350", year = 2006,
            engine = "M272", fuel = listOf("petrol", "lpg")
        )
        coEvery { api.createSession(vehicle) } returns session

        assertEquals(session, repository.createSession(vehicle))
        coVerify(exactly = 1) { api.createSession(vehicle) }
    }

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
    fun updateSymptomTrimsTextAndUsesSelectedIds() = runTest {
        coEvery { api.updateSymptom("session-1", "symptom-1", any<SymptomRequest>()) } returns session

        assertEquals(session, repository.updateSymptom("session-1", "symptom-1", "  rough idle  "))

        coVerify {
            api.updateSymptom("session-1", "symptom-1", match {
                it.raw_text == "rough idle" && it.symptom == "rough idle"
            })
        }
    }

    @Test
    fun updateDtcNormalizesCodeAndUsesDtcId() = runTest {
        coEvery { api.updateDtc("session-1", "dtc-1", any<DtcRequest>()) } returns session

        assertEquals(session, repository.updateDtc("session-1", "dtc-1", " p0302 "))

        coVerify { api.updateDtc("session-1", "dtc-1", match { it.code == "P0302" }) }
    }

    @Test
    fun deleteSymptomDelegatesToApi() = runTest {
        coEvery { api.deleteSymptom("session-1", "symptom-1") } returns session

        assertEquals(session, repository.deleteSymptom("session-1", "symptom-1"))

        coVerify(exactly = 1) { api.deleteSymptom("session-1", "symptom-1") }
    }

    @Test
    fun deleteDtcDelegatesToApi() = runTest {
        coEvery { api.deleteDtc("session-1", "dtc-1") } returns session

        assertEquals(session, repository.deleteDtc("session-1", "dtc-1"))

        coVerify(exactly = 1) { api.deleteDtc("session-1", "dtc-1") }
    }

    @Test
    fun recordTestResultForwardsResultNotesAndLanguage() = runTest {
        coEvery { api.recordTestResult("session-1", any<TestResultRequest>(), "hy") } returns session

        assertEquals(session, repository.recordTestResult("session-1", "test-1", "FAIL", "pressure low", "hy"))

        coVerify {
            api.recordTestResult("session-1", match {
                it.test_id == "test-1" && it.result == "FAIL" && it.notes == "pressure low"
            }, "hy")
        }
    }

    @Test
    fun analyzePassesRequestedLanguage() = runTest {
        coEvery { api.analyze("session-1", "hy") } returns session

        assertEquals(session, repository.analyze("session-1", "hy"))

        coVerify(exactly = 1) { api.analyze("session-1", "hy") }
    }
}
