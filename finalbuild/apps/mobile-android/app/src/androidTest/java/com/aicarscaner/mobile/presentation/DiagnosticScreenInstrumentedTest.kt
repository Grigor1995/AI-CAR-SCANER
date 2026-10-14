package com.aicarscaner.mobile.presentation

import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.test.performTextClearance
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.aicarscaner.mobile.data.api.AuditEventDto
import com.aicarscaner.mobile.data.api.DiagnosticApi
import com.aicarscaner.mobile.data.api.DiagnosticSessionDto
import com.aicarscaner.mobile.data.api.EvidenceDto
import com.aicarscaner.mobile.data.api.HypothesisDto
import com.aicarscaner.mobile.data.api.DtcDto
import com.aicarscaner.mobile.data.api.DtcRequest
import com.aicarscaner.mobile.data.api.RecommendationDto
import com.aicarscaner.mobile.data.api.SymptomDto
import com.aicarscaner.mobile.data.api.SymptomRequest
import com.aicarscaner.mobile.data.api.TestResultDto
import com.aicarscaner.mobile.data.api.TestResultRequest
import com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto
import com.aicarscaner.mobile.data.api.VehicleDto
import com.aicarscaner.mobile.data.repository.DiagnosticRepository
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class DiagnosticScreenInstrumentedTest {
    @get:Rule
    val composeRule = createAndroidComposeRule<TestHostActivity>()

    private val fakeApi = FakeDiagnosticApi()

    private fun launchScreen() {
        // Keep UI assertions deterministic regardless of preferences left on the emulator.
        composeRule.activity
            .getSharedPreferences("ai_car_scaner_settings", android.content.Context.MODE_PRIVATE)
            .edit()
            .clear()
            .commit()

        composeRule.setContent {
            DiagnosticScreen(
                DiagnosticViewModel(
                    DiagnosticRepository(fakeApi)
                )
            )
        }
        composeRule.waitForIdle()
    }

    private fun createSession() {
        composeRule.onNodeWithText("Create Diagnostic Session")
            .performScrollTo()
            .performClick()
        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("Diagnose (0)")
                .fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun screenShowsInitialVehicleForm() {
        launchScreen()

        composeRule.onNodeWithText("AI CAR SCANER").assertExists()
        composeRule.onNodeWithText("New Session").assertExists()
        composeRule.onNodeWithText("Create Diagnostic Session")
            .performScrollTo()
            .assertExists()
    }

    @Test
    fun creatingSessionShowsDiagnosticTabsAndVehicle() {
        launchScreen()
        createSession()

        composeRule.onNodeWithText("OBD").assertExists()
        composeRule.onNodeWithText("Live Data").assertExists()
        composeRule.onNodeWithText("Analysis").assertExists()
        composeRule.onNodeWithText("E-Class", substring = true).assertExists()
    }

    @Test
    fun addingSymptomUpdatesDiagnosticListAndTabCount() {
        launchScreen()
        createSession()

        composeRule.onNodeWithText("Driver symptom")
            .performScrollTo()
            .performTextInput("Engine shakes at low RPM")
        composeRule.onNodeWithText("Add Symptom")
            .performScrollTo()
            .performClick()

        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("Engine shakes at low RPM")
                .fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onNodeWithText("Diagnose (1)").assertExists()
    }

    @Test
    fun addingDtcUpdatesDiagnosticTabCount() {
        launchScreen()
        createSession()

        composeRule.onNodeWithText("Diagnostic trouble code")
            .performScrollTo()
            .performTextInput("p0302")
        composeRule.onNodeWithText("Add DTC")
            .performScrollTo()
            .performClick()

        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("Diagnose (1)")
                .fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun settingsDialogCanSwitchToArmenianAndClose() {
        launchScreen()

        composeRule.onNodeWithText("⚙").performClick()
        composeRule.onNodeWithText("ARM").performClick()

        composeRule.onNodeWithText("Նոր սեսիա").assertExists()
        composeRule.onNodeWithText("Կարգավորումներ").assertExists()
        composeRule.onNodeWithText("Փակել").performClick()
        composeRule.onNodeWithText("Ստեղծել ախտորոշիչ սեսիա")
            .performScrollTo()
            .assertExists()
    }

    @Test
    fun newSessionDialogCanBeCancelledOrConfirmed() {
        launchScreen()
        createSession()

        composeRule.onNodeWithContentDescription("New Session").performClick()
        composeRule.onNodeWithText("Start a new session?").assertExists()
        composeRule.onNodeWithText("Cancel").performClick()
        composeRule.onNodeWithText("Diagnose (0)").assertExists()

        composeRule.onNodeWithContentDescription("New Session").performClick()
        composeRule.onNodeWithText("Start New Session").performClick()
        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("Create Diagnostic Session")
                .fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onNodeWithText("Create Diagnostic Session").assertExists()
    }


    @Test
    fun symptomCanBeEditedAndDeleted() {
        launchScreen()
        createSession()

        composeRule.onNodeWithText("Driver symptom")
            .performScrollTo()
            .performTextInput("Engine shakes at low RPM")
        composeRule.onNodeWithText("Add Symptom")
            .performScrollTo()
            .performClick()

        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("Engine shakes at low RPM")
                .fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithText("Edit").performScrollTo().performClick()
        composeRule.onNodeWithText("Driver symptom").performTextClearance()
        composeRule.onNodeWithText("Driver symptom").performTextInput("Engine shakes after warm-up")
        composeRule.onNodeWithText("Save").performScrollTo().performClick()

        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("Engine shakes after warm-up")
                .fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithText("Delete").performScrollTo().performClick()
        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("Diagnose (0)")
                .fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun dtcCanBeEditedAndDeleted() {
        launchScreen()
        createSession()

        composeRule.onNodeWithText("Diagnostic trouble code")
            .performScrollTo()
            .performTextInput("p0302")
        composeRule.onNodeWithText("Add DTC")
            .performScrollTo()
            .performClick()

        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("P0302")
                .fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithText("Edit").performScrollTo().performClick()
        composeRule.onNodeWithText("Diagnostic trouble code").performTextClearance()
        composeRule.onNodeWithText("Diagnostic trouble code").performTextInput("P0300")
        composeRule.onNodeWithText("Save").performScrollTo().performClick()

        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("P0300")
                .fetchSemanticsNodes().isNotEmpty()
        }

        composeRule.onNodeWithText("Delete").performScrollTo().performClick()
        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("Diagnose (0)")
                .fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun analysisRendersEvidenceHypothesisRecommendationsAndRecordsResult() {
        launchScreen()
        createSession()

        composeRule.onNodeWithText("Driver symptom")
            .performScrollTo()
            .performTextInput("Engine shakes on LPG under load")
        composeRule.onNodeWithText("Add Symptom")
            .performScrollTo()
            .performClick()

        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("Review Analysis")
                .fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onNodeWithText("Review Analysis").performScrollTo().performClick()

        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("LPG injector imbalance could explain load misfire")
                .fetchSemanticsNodes().isNotEmpty()
        }
        assertTrue(composeRule.onAllNodesWithText("Petrol runs normally", substring = true)
            .fetchSemanticsNodes().isNotEmpty())
        assertTrue(composeRule.onAllNodesWithText("Check LPG injector balance", substring = true)
            .fetchSemanticsNodes().isNotEmpty())
        assertTrue(composeRule.onAllNodesWithText("Does misfire disappear on petrol?", substring = true)
            .fetchSemanticsNodes().isNotEmpty())

        composeRule.onAllNodesWithText("Record result")[0].performScrollTo().performClick()
        composeRule.onNodeWithText("FAIL").performClick()
        composeRule.onNodeWithText("Technician notes / result")
            .performTextInput("Injector balance uneven")
        run {
            val resultButtons = composeRule.onAllNodesWithText("Record result")
            resultButtons[resultButtons.fetchSemanticsNodes().lastIndex].performClick()
        }

        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("Injector balance uneven")
                .fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun liveDataTabShowsDisconnectedStateWhenNoObdAdapterIsConnected() {
        launchScreen()
        createSession()

        composeRule.onNodeWithText("Live Data").performClick()
        composeRule.waitForIdle()

        assertTrue(composeRule.onAllNodesWithText("OBD is not connected")
            .fetchSemanticsNodes().isNotEmpty())
    }


    @Test
    fun vehicleCanEnterEditModeAndSave() {
        launchScreen()
        createSession()

        // The first exact "Session" is the summary card heading; the second is the tab.
        composeRule.onAllNodesWithText("Session")[1].performClick()
        composeRule.onNodeWithText("Edit").performScrollTo().performClick()

        composeRule.onNodeWithText("Save Session").performScrollTo().assertExists()
        composeRule.onNodeWithText("Save Session").performClick()

        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("Edit").fetchSemanticsNodes().isNotEmpty()
        }
        assertTrue(
            composeRule.onAllNodesWithText("E-Class", substring = true)
                .fetchSemanticsNodes().isNotEmpty()
        )
    }

    @Test
    fun wifiConnectButtonRequiresANonBlankHost() {
        launchScreen()
        createSession()

        composeRule.onNodeWithText("OBD").performScrollTo().performClick()
        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("OBD Connection")
                .fetchSemanticsNodes().isNotEmpty()
        }
        // The UI uses U+2011 (non-breaking hyphen) in "Wi‑Fi".
        composeRule.onNodeWithText("Wi‑Fi").performScrollTo().performClick()

        composeRule.onNodeWithText("Connect Wi‑Fi").assertIsNotEnabled()
        composeRule.onNodeWithText("Host").performTextInput("192.0.2.10")
        composeRule.onNodeWithText("Connect Wi‑Fi").assertIsEnabled()
    }

    @Test
    fun testResultDialogCanBeCancelledWithoutSavingAResult() {
        launchScreen()
        createSession()

        composeRule.onNodeWithText("Driver symptom")
            .performScrollTo()
            .performTextInput("Engine shakes on LPG under load")
        composeRule.onNodeWithText("Add Symptom")
            .performScrollTo()
            .performClick()

        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("Review Analysis").fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onNodeWithText("Review Analysis").performScrollTo().performClick()

        composeRule.waitUntil(5_000) {
            composeRule.onAllNodesWithText("Check LPG injector balance")
                .fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onAllNodesWithText("Record result")[0].performScrollTo().performClick()
        composeRule.onNodeWithText("Cancel").performClick()

        assertTrue(
            composeRule.onAllNodesWithText("Check LPG injector balance")
                .fetchSemanticsNodes().isNotEmpty()
        )
        assertTrue(
            composeRule.onAllNodesWithText("Result: INCOMPLETE")
                .fetchSemanticsNodes().isEmpty()
        )
    }

}

private class FakeDiagnosticApi : DiagnosticApi {
    private var current = DiagnosticSessionDto(
        session_id = "session-test-123456",
        state = "CREATED"
    )

    override suspend fun vehicleCatalog(): List<VehicleCatalogEntryDto> = listOf(
        VehicleCatalogEntryDto(
            make = "Mercedes-Benz",
            model = "E-Class",
            chassis = "W211",
            year = 2006,
            engine = "M272 E35 3.5",
            ecu = "ME9.7",
            fuel = listOf("petrol", "lpg"),
            source = "instrumentation-test",
            scope = "test"
        )
    )

    override suspend fun createSession(vehicle: VehicleDto): DiagnosticSessionDto =
        current.copy(state = "VEHICLE_IDENTIFIED", vehicle = vehicle).also { current = it }

    override suspend fun updateVehicle(
        sessionId: String,
        vehicle: VehicleDto
    ): DiagnosticSessionDto = current.copy(vehicle = vehicle).also { current = it }

    override suspend fun addSymptom(
        sessionId: String,
        request: SymptomRequest
    ): DiagnosticSessionDto = current.copy(
        symptoms = current.symptoms + SymptomDto(
            id = "symptom-${current.symptoms.size + 1}",
            raw_text = request.raw_text,
            normalized = request.normalized
        )
    ).also { current = it }

    override suspend fun updateSymptom(
        sessionId: String,
        symptomId: String,
        request: SymptomRequest
    ): DiagnosticSessionDto = current.copy(
        symptoms = current.symptoms.map {
            if (it.id == symptomId) it.copy(raw_text = request.raw_text, normalized = request.normalized) else it
        }
    ).also { current = it }

    override suspend fun deleteSymptom(
        sessionId: String,
        symptomId: String
    ): DiagnosticSessionDto = current.copy(
        symptoms = current.symptoms.filterNot { it.id == symptomId }
    ).also { current = it }

    override suspend fun addDtc(
        sessionId: String,
        request: DtcRequest
    ): DiagnosticSessionDto = current.copy(
        dtcs = current.dtcs + DtcDto(
            id = "dtc-${current.dtcs.size + 1}",
            code = request.code,
            description = request.description
        )
    ).also { current = it }

    override suspend fun updateDtc(
        sessionId: String,
        dtcId: String,
        request: DtcRequest
    ): DiagnosticSessionDto = current.copy(
        dtcs = current.dtcs.map {
            if (it.id == dtcId) it.copy(code = request.code, description = request.description) else it
        }
    ).also { current = it }

    override suspend fun deleteDtc(
        sessionId: String,
        dtcId: String
    ): DiagnosticSessionDto = current.copy(
        dtcs = current.dtcs.filterNot { it.id == dtcId }
    ).also { current = it }

    override suspend fun recordTestResult(
        sessionId: String,
        request: TestResultRequest,
        language: String
    ): DiagnosticSessionDto = current.copy(
        test_results = current.test_results + TestResultDto(
            test_id = request.test_id,
            result = request.result,
            measurements = request.measurements,
            notes = request.notes
        )
    ).also { current = it }

    override suspend fun analyze(
        sessionId: String,
        language: String
    ): DiagnosticSessionDto = current.copy(
        state = "INITIAL_ANALYSIS",
        evidence = listOf(
            EvidenceDto(
                id = "evidence-petrol",
                fact = "Petrol runs normally",
                source = "driver report",
                status = "reported",
                confidence = 0.9
            )
        ),
        hypotheses = listOf(
            HypothesisDto(
                id = "hypothesis-lpg",
                category = "Fuel delivery",
                statement = "LPG injector imbalance could explain load misfire",
                supporting_evidence_ids = listOf("evidence-petrol"),
                status = "POSSIBLE:0.72"
            )
        ),
        recommendations = listOf(
            RecommendationDto(
                id = "lpg-injector-balance",
                title = "Check LPG injector balance",
                purpose = "Compare injector contribution under the same operating conditions",
                priority = 0.9,
                expected_observation = "Uneven contribution supports a fuel-delivery hypothesis",
                informationGain = 0.7,
                estimatedCost = 15.0,
                riskLevel = "LOW"
            )
        ),
        audit_log = current.audit_log + AuditEventDto(
            event = "analysis_requested",
            questions = listOf("Does misfire disappear on petrol?")
        )
    ).also { current = it }
}
