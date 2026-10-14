package com.aicarscaner.mobile.presentation

import android.Manifest
import androidx.activity.ComponentActivity
import androidx.compose.ui.test.assertExists
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.waitUntil
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.rule.GrantPermissionRule
import com.aicarscaner.mobile.data.api.AuditEventDto
import com.aicarscaner.mobile.data.api.DiagnosticApi
import com.aicarscaner.mobile.data.api.DiagnosticSessionDto
import com.aicarscaner.mobile.data.api.DtcDto
import com.aicarscaner.mobile.data.api.DtcRequest
import com.aicarscaner.mobile.data.api.SymptomDto
import com.aicarscaner.mobile.data.api.SymptomRequest
import com.aicarscaner.mobile.data.api.TestResultDto
import com.aicarscaner.mobile.data.api.TestResultRequest
import com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto
import com.aicarscaner.mobile.data.api.VehicleDto
import com.aicarscaner.mobile.data.repository.DiagnosticRepository
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.rules.RuleChain
import org.junit.rules.TestRule

@RunWith(AndroidJUnit4::class)
class DiagnosticScreenInstrumentedTest {
    private val composeRule = createAndroidComposeRule<ComponentActivity>()

    @get:Rule
    val ruleChain: TestRule = RuleChain
        .outerRule(
            GrantPermissionRule.grant(
                Manifest.permission.BLUETOOTH_CONNECT,
                Manifest.permission.BLUETOOTH_SCAN
            )
        )
        .around(composeRule)

    private val fakeApi = FakeDiagnosticApi()

    private fun launchScreen() {
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
        composeRule.onNodeWithText("E-Class").assertExists()
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
        audit_log = current.audit_log + AuditEventDto(event = "analysis_requested")
    ).also { current = it }
}
