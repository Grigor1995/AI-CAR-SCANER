package com.aicarscaner.mobile.presentation

import com.aicarscaner.mobile.data.api.DiagnosticSessionDto
import com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto
import com.aicarscaner.mobile.data.api.VehicleDto
import com.aicarscaner.mobile.data.api.HypothesisDto
import com.aicarscaner.mobile.data.api.RecommendationDto
import com.aicarscaner.mobile.data.api.TestResultDto
import com.aicarscaner.mobile.data.repository.DiagnosticRepository
import io.mockk.every
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
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

    private val repository = mockk<DiagnosticRepository> {
        every { offlineVehicleCatalog() } returns emptyList()
    }
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
    fun httpFailureWithoutBodyIncludesOnlyStatusCode() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel = DiagnosticViewModel(repository)
        val response = Response.error<DiagnosticSessionDto>(
            503,
            "".toResponseBody("text/plain".toMediaType())
        )
        coEvery { repository.createSession(vehicle) } throws HttpException(response)

        viewModel.createSession(vehicle)
        advanceUntilIdle()

        assertEquals("HTTP 503", viewModel.uiState.value.error)
        assertFalse(viewModel.uiState.value.loading)
    }

    @Test
    fun httpFailureTruncatesErrorBodyToFiveHundredCharacters() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel = DiagnosticViewModel(repository)
        val body = "x".repeat(600)
        val response = Response.error<DiagnosticSessionDto>(
            502,
            body.toResponseBody("text/plain".toMediaType())
        )
        coEvery { repository.createSession(vehicle) } throws HttpException(response)

        viewModel.createSession(vehicle)
        advanceUntilIdle()

        assertEquals("HTTP 502: " + "x".repeat(500), viewModel.uiState.value.error)
    }

    @Test
    fun nullThrowableMessageUsesFallbackText() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel = DiagnosticViewModel(repository)
        coEvery { repository.createSession(vehicle) } throws Throwable()

        viewModel.createSession(vehicle)
        advanceUntilIdle()

        assertEquals("Request failed", viewModel.uiState.value.error)
        assertFalse(viewModel.uiState.value.loading)
    }

    @Test
    fun failedActionKeepsLastSuccessfulSession() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel = DiagnosticViewModel(repository)
        coEvery { repository.createSession(vehicle) } returns session
        coEvery { repository.addSymptom("session-1", "rough idle") } throws IllegalStateException("server unavailable")

        viewModel.createSession(vehicle)
        advanceUntilIdle()
        viewModel.addSymptom("rough idle")
        advanceUntilIdle()

        assertEquals(session, viewModel.uiState.value.session)
        assertEquals("server unavailable", viewModel.uiState.value.error)
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
    fun everyTestOutcomePublishesTheRecalculatedSessionWithoutASecondAnalysis() = runTest(mainDispatcherRule.dispatcher) {
        for (outcome in listOf("PASS", "FAIL", "INCOMPLETE")) {
            val viewModel = DiagnosticViewModel(repository)
            coEvery { repository.createSession(vehicle) } returns session
            viewModel.createSession(vehicle)
            advanceUntilIdle()
            val pending = CompletableDeferred<DiagnosticSessionDto>()
            coEvery { repository.recordTestResult("session-1", "test-1", outcome, "measurement", "hy") } coAnswers { pending.await() }
            val recalculated = session.copy(
                state="HYPOTHESIS_VALIDATION",
                hypotheses=listOf(HypothesisDto("h1", "ignition", "Updated after $outcome", status="possible:0.65")),
                recommendations=listOf(RecommendationDto("test-2", "Follow-up", "Isolate the cause", .8)),
                test_results=listOf(TestResultDto("test-1", outcome)))
            viewModel.recordTestResult("test-1", outcome, "measurement", "hy")
            runCurrent()
            assertTrue(viewModel.uiState.value.loading)
            assertEquals(0, viewModel.uiState.value.testResultRevision)
            pending.complete(recalculated)
            advanceUntilIdle()
            assertEquals(recalculated, viewModel.uiState.value.session)
            assertEquals(1, viewModel.uiState.value.testResultRevision)
            assertFalse(viewModel.uiState.value.loading)
        }
        coVerify(exactly=0) { repository.analyze(any(), any()) }
    }

    @Test
    fun failedTestSubmissionKeepsThePreviousDiagnosisAndDoesNotReportRecalculation() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel=DiagnosticViewModel(repository)
        coEvery {repository.createSession(vehicle)} returns session
        coEvery {repository.recordTestResult("session-1", "test-1", "FAIL", null, "en")} throws IllegalStateException("offline")
        viewModel.createSession(vehicle)
        advanceUntilIdle()
        viewModel.recordTestResult("test-1", "FAIL", null)
        advanceUntilIdle()
        assertEquals(session,viewModel.uiState.value.session)
        assertEquals(0,viewModel.uiState.value.testResultRevision)
        assertEquals("offline",viewModel.uiState.value.error)
        assertEquals(1,viewModel.uiState.value.testResultCompletion)
        viewModel.recordTestResult("test-1", "FAIL", null)
        advanceUntilIdle()
        assertEquals(2,viewModel.uiState.value.testResultCompletion)
        assertEquals(0,viewModel.uiState.value.testResultRevision)
        assertFalse(viewModel.uiState.value.loading)
    }

    @Test
    fun saveIsIndependentOfOtherRequestsAndDuplicateTapsAreIgnored() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel=DiagnosticViewModel(repository)
        coEvery {repository.createSession(vehicle)} returns session
        viewModel.createSession(vehicle)
        advanceUntilIdle()
        val analysis=CompletableDeferred<DiagnosticSessionDto>()
        val saved=CompletableDeferred<DiagnosticSessionDto>()
        coEvery {repository.analyze("session-1", "en")} coAnswers {analysis.await()}
        coEvery {repository.recordTestResult("session-1", "test-1", "PASS", null, "en")} coAnswers {saved.await()}
        viewModel.analyze()
        runCurrent()
        viewModel.recordTestResult("test-1", "PASS", null)
        viewModel.recordTestResult("test-1", "PASS", null)
        assertTrue(viewModel.uiState.value.testResultSaving)
        runCurrent()
        val updated=session.copy(state="HYPOTHESIS_VALIDATION",test_results=listOf(TestResultDto("test-1", "PASS")))
        saved.complete(updated)
        runCurrent()
        assertFalse(viewModel.uiState.value.testResultSaving)
        assertEquals(updated,viewModel.uiState.value.session)
        analysis.complete(session)
        advanceUntilIdle()
        assertEquals(updated,viewModel.uiState.value.session)
        coVerify(exactly=1) {repository.recordTestResult("session-1", "test-1", "PASS", null, "en")}
    }

    @Test
    fun timedOutSaveUnlocksRetryWithoutLosingTheDiagnosis() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel=DiagnosticViewModel(repository)
        coEvery {repository.createSession(vehicle)} returns session
        viewModel.createSession(vehicle)
        advanceUntilIdle()
        coEvery {repository.recordTestResult("session-1", "test-1", "FAIL", null, "en")} coAnswers {CompletableDeferred<DiagnosticSessionDto>().await()}
        viewModel.recordTestResult("test-1", "FAIL", null)
        advanceUntilIdle()
        assertFalse(viewModel.uiState.value.testResultSaving)
        assertTrue(viewModel.uiState.value.testResultError!!.contains("timed out"))
        assertEquals(session,viewModel.uiState.value.session)
        coEvery {repository.recordTestResult("session-1", "test-1", "FAIL", null, "en")} returns session
        viewModel.recordTestResult("test-1", "FAIL", null)
        advanceUntilIdle()
        assertNull(viewModel.uiState.value.testResultError)
        assertEquals(1,viewModel.uiState.value.testResultRevision)
    }

    @Test
    fun openingAnotherSessionClearsThePreviousTestUpdateNotice() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel=DiagnosticViewModel(repository)
        coEvery {repository.createSession(vehicle)} returns session
        coEvery {repository.recordTestResult("session-1", "test-1", "PASS", null, "en")} returns session
        coEvery {repository.getSession("other", "en")} returns session.copy(session_id="other")
        viewModel.createSession(vehicle)
        advanceUntilIdle()
        viewModel.recordTestResult("test-1", "PASS", null)
        advanceUntilIdle()
        assertEquals(1,viewModel.uiState.value.testResultRevision)
        viewModel.openSession("other")
        advanceUntilIdle()
        assertEquals(0,viewModel.uiState.value.testResultRevision)
    }

    @Test
    fun loadingStaysTrueUntilPendingSessionRequestCompletes() = runTest(mainDispatcherRule.dispatcher) {
        val pending = CompletableDeferred<DiagnosticSessionDto>()
        val viewModel = DiagnosticViewModel(repository)
        coEvery { repository.createSession(vehicle) } coAnswers { pending.await() }

        viewModel.createSession(vehicle)
        runCurrent()

        assertTrue(viewModel.uiState.value.loading)
        assertNull(viewModel.uiState.value.session)
        assertNull(viewModel.uiState.value.error)

        pending.complete(session)
        advanceUntilIdle()

        assertEquals(session, viewModel.uiState.value.session)
        assertFalse(viewModel.uiState.value.loading)
        assertNull(viewModel.uiState.value.error)
    }

    @Test
    fun everySessionDependentActionRejectsMissingSession() = runTest(mainDispatcherRule.dispatcher) {
        val viewModel = DiagnosticViewModel(repository)
        val actions: List<() -> Unit> = listOf(
            { viewModel.updateVehicle(vehicle) },
            { viewModel.updateSymptom("symptom-1", "rough idle") },
            { viewModel.deleteSymptom("symptom-1") },
            { viewModel.addDtc("P0302") },
            { viewModel.updateDtc("dtc-1", "P0300") },
            { viewModel.deleteDtc("dtc-1") },
            { viewModel.analyze() },
            { viewModel.recordTestResult("check-ignition", "INCOMPLETE", null) }
        )

        actions.forEach { action ->
            action()
            advanceUntilIdle()
            assertEquals("Create a session first", viewModel.uiState.value.error)
            assertNull(viewModel.uiState.value.session)
            assertFalse(viewModel.uiState.value.loading)
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
    @Test fun repeatedLiveRefreshIsCoalescedAndSessionSwitchDropsOldResponse() = runTest(mainDispatcherRule.dispatcher) {
        val vm = DiagnosticViewModel(repository)
        coEvery { repository.getSession("session-1", "en") } returns session
        coEvery { repository.getSession("session-2", "en") } returns session.copy(session_id="session-2")
        val pending=CompletableDeferred<com.aicarscaner.mobile.data.api.BackendLiveRecordsDto>()
        coEvery { repository.acquisitionRecords("session-1", any()) } coAnswers { pending.await() }
        vm.openSession("session-1"); advanceUntilIdle()
        vm.refreshBackendLiveRecords(); vm.refreshBackendLiveRecords(); runCurrent()
        coVerify(exactly=1) { repository.acquisitionRecords("session-1", any()) }
        assertTrue(vm.uiState.value.backendLiveLoading)
        vm.openSession("session-2"); runCurrent()
        pending.complete(com.aicarscaner.mobile.data.api.BackendLiveRecordsDto(listOf(com.aicarscaner.mobile.data.api.BackendLiveRecordDto(channel="old",numeric_value=750.0))))
        advanceUntilIdle()
        assertTrue(vm.uiState.value.backendLiveRecords.isEmpty())
        assertFalse(vm.uiState.value.backendLiveLoading)
    }

    @Test fun catalogFailureAfterSuccessMarksOfflineWithoutLosingSelectionRows() = runTest(mainDispatcherRule.dispatcher) {
        val vm=DiagnosticViewModel(repository)
        val row=VehicleCatalogEntryDto("Toyota","Corolla","E210",2020,"Hybrid")
        coEvery { repository.vehicleCatalog() } returns listOf(row)
        vm.loadVehicleCatalog(); advanceUntilIdle()
        assertTrue(vm.uiState.value.catalogOnline)
        coEvery { repository.vehicleCatalog() } throws IllegalStateException("offline")
        vm.loadVehicleCatalog(); advanceUntilIdle()
        assertFalse(vm.uiState.value.catalogOnline)
        assertEquals(listOf(row),vm.uiState.value.vehicleCatalog)
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
