package com.aicarscaner.mobile.presentation

import androidx.lifecycle.ViewModel
import com.aicarscaner.mobile.data.api.DiagnosticSessionDto
import com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto
import com.aicarscaner.mobile.data.api.VehicleDto
import com.aicarscaner.mobile.data.repository.DiagnosticRepository
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TestWatcher
import org.junit.runner.Description
import retrofit2.HttpException
import retrofit2.Response

@OptIn(ExperimentalCoroutinesApi::class)
class DiagnosticViewModelTest {
    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private val repository = mockk<DiagnosticRepository>()
    private val vehicle = VehicleDto(
        make = "Mercedes-Benz",
        model = "E350",
        chassis = "W211",
        year = 2006,
        engine = "M272",
        fuel = listOf("petrol", "lpg")
    )
    private val session = DiagnosticSessionDto(session_id = "session-1", state = "COLLECTING")
    private val updatedSession = DiagnosticSessionDto(session_id = "session-1", state = "TESTING")

    @Test
    fun initialStateIsEmptyAndNotLoading() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel = DiagnosticViewModel(repository)

        assertNull(viewModel.uiState.value.session)
        assertTrue(viewModel.uiState.value.vehicleCatalog.isEmpty())
        assertFalse(viewModel.uiState.value.loading)
        assertNull(viewModel.uiState.value.error)
    }

    @Test
    fun loadVehicleCatalogPublishesEntries() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel = DiagnosticViewModel(repository)
        val catalog = listOf(
            VehicleCatalogEntryDto(
                make = "Mercedes-Benz", model = "E-Class", chassis = "W211",
                year = 2006, engine = "M272"
            )
        )
        coEvery { repository.vehicleCatalog() } returns catalog

        viewModel.loadVehicleCatalog()
        advanceUntilIdle()

        assertEquals(catalog, viewModel.uiState.value.vehicleCatalog)
        assertNull(viewModel.uiState.value.error)
    }

    @Test
    fun loadVehicleCatalogFailureIsSilentAndDoesNotBlockFallback() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel = DiagnosticViewModel(repository)
        coEvery { repository.vehicleCatalog() } throws IllegalStateException("offline")

        viewModel.loadVehicleCatalog()
        advanceUntilIdle()

        assertTrue(viewModel.uiState.value.vehicleCatalog.isEmpty())
        assertNull(viewModel.uiState.value.error)
        assertFalse(viewModel.uiState.value.loading)
    }

    @Test
    fun createSessionUpdatesUiState() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel = DiagnosticViewModel(repository)
        coEvery { repository.createSession(vehicle) } returns session

        viewModel.createSession(vehicle)
        advanceUntilIdle()

        assertEquals(session, viewModel.uiState.value.session)
        assertFalse(viewModel.uiState.value.loading)
        assertNull(viewModel.uiState.value.error)
        coVerify(exactly = 1) { repository.createSession(vehicle) }
    }

    @Test
    fun ordinaryFailureIsPublishedAndLoadingIsCleared() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel = DiagnosticViewModel(repository)
        coEvery { repository.createSession(vehicle) } throws IllegalStateException("network unavailable")

        viewModel.createSession(vehicle)
        advanceUntilIdle()

        assertEquals("network unavailable", viewModel.uiState.value.error)
        assertFalse(viewModel.uiState.value.loading)
        assertNull(viewModel.uiState.value.session)
    }

    @Test
    fun httpFailureIncludesStatusAndErrorBody() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel = DiagnosticViewModel(repository)
        val response = Response.error<DiagnosticSessionDto>(
            400,
            "invalid vehicle".toResponseBody("text/plain".toMediaType())
        )
        coEvery { repository.createSession(vehicle) } throws HttpException(response)

        viewModel.createSession(vehicle)
        advanceUntilIdle()

        assertEquals("HTTP 400: invalid vehicle", viewModel.uiState.value.error)
        assertFalse(viewModel.uiState.value.loading)
    }

    @Test
    fun clearSessionRemovesSessionAndKeepsLoadedCatalog() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel = DiagnosticViewModel(repository)
        val catalog = listOf(
            VehicleCatalogEntryDto(
                make = "BMW", model = "3 Series", chassis = "E90",
                year = 2008, engine = "N52"
            )
        )
        coEvery { repository.vehicleCatalog() } returns catalog
        coEvery { repository.createSession(vehicle) } returns session

        viewModel.loadVehicleCatalog()
        advanceUntilIdle()
        viewModel.createSession(vehicle)
        advanceUntilIdle()
        viewModel.clearSession()

        assertNull(viewModel.uiState.value.session)
        assertEquals(catalog, viewModel.uiState.value.vehicleCatalog)
        assertFalse(viewModel.uiState.value.loading)
        assertNull(viewModel.uiState.value.error)
    }

    @Test
    fun allSessionActionsForwardSessionIdAndArguments() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel = DiagnosticViewModel(repository)
        coEvery { repository.createSession(vehicle) } returns session
        coEvery { repository.updateVehicle("session-1", vehicle) } returns updatedSession
        coEvery { repository.addSymptom("session-1", "rough idle") } returns updatedSession
        coEvery { repository.updateSymptom("session-1", "symptom-1", "engine shakes") } returns updatedSession
        coEvery { repository.deleteSymptom("session-1", "symptom-1") } returns updatedSession
        coEvery { repository.addDtc("session-1", "P0302") } returns updatedSession
        coEvery { repository.updateDtc("session-1", "dtc-1", "P0300") } returns updatedSession
        coEvery { repository.deleteDtc("session-1", "dtc-1") } returns updatedSession
        coEvery { repository.analyze("session-1", "hy") } returns updatedSession
        coEvery {
            repository.recordTestResult("session-1", "fuel-pressure", "PASS", "pressure stable", "hy")
        } returns updatedSession

        viewModel.createSession(vehicle)
        advanceUntilIdle()
        viewModel.updateVehicle(vehicle)
        advanceUntilIdle()
        viewModel.addSymptom("rough idle")
        advanceUntilIdle()
        viewModel.updateSymptom("symptom-1", "engine shakes")
        advanceUntilIdle()
        viewModel.deleteSymptom("symptom-1")
        advanceUntilIdle()
        viewModel.addDtc("P0302")
        advanceUntilIdle()
        viewModel.updateDtc("dtc-1", "P0300")
        advanceUntilIdle()
        viewModel.deleteDtc("dtc-1")
        advanceUntilIdle()
        viewModel.analyze("hy")
        advanceUntilIdle()
        viewModel.recordTestResult("fuel-pressure", "PASS", "pressure stable", "hy")
        advanceUntilIdle()

        assertEquals(updatedSession, viewModel.uiState.value.session)
        assertFalse(viewModel.uiState.value.loading)
        assertNull(viewModel.uiState.value.error)
        coVerify(exactly = 1) { repository.updateVehicle("session-1", vehicle) }
        coVerify(exactly = 1) { repository.addSymptom("session-1", "rough idle") }
        coVerify(exactly = 1) { repository.updateSymptom("session-1", "symptom-1", "engine shakes") }
        coVerify(exactly = 1) { repository.deleteSymptom("session-1", "symptom-1") }
        coVerify(exactly = 1) { repository.addDtc("session-1", "P0302") }
        coVerify(exactly = 1) { repository.updateDtc("session-1", "dtc-1", "P0300") }
        coVerify(exactly = 1) { repository.deleteDtc("session-1", "dtc-1") }
        coVerify(exactly = 1) { repository.analyze("session-1", "hy") }
        coVerify(exactly = 1) {
            repository.recordTestResult("session-1", "fuel-pressure", "PASS", "pressure stable", "hy")
        }
    }

    @Test
    fun actionWithoutSessionProducesHelpfulError() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel = DiagnosticViewModel(repository)

        viewModel.addSymptom("rough idle")
        advanceUntilIdle()

        assertEquals("Create a session first", viewModel.uiState.value.error)
        assertFalse(viewModel.uiState.value.loading)
    }
}

@OptIn(ExperimentalCoroutinesApi::class)
class MainDispatcherRule(
    val dispatcher: TestDispatcher = StandardTestDispatcher()
) : TestWatcher() {
    override fun starting(description: Description) {
        Dispatchers.setMain(dispatcher)
    }

    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}
