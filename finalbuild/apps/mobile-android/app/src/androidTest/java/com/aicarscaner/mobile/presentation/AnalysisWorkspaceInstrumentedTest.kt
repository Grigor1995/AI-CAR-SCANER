package com.aicarscaner.mobile.presentation

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.aicarscaner.mobile.data.api.*
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AnalysisWorkspaceInstrumentedTest {
    @get:Rule val compose=createAndroidComposeRule<TestHostActivity>()

    @Test fun testsAreInAnalysisAndNewResultReturnsToTheUpdatedDiagnosis() {
        val original=DiagnosticSessionDto("session-1","TESTING",
            hypotheses=listOf(HypothesisDto("h1","Ignition","Original diagnosis",status="possible:0.25")),
            recommendations=listOf(RecommendationDto("test-1","Fuel pressure check","Measure",.8)))
        val recalculated=original.copy(
            hypotheses=listOf(HypothesisDto("h1","Ignition","Recalculated diagnosis",status="supported_by_test:0.8")),
            recommendations=listOf(RecommendationDto("test-2","Injector follow-up","Isolate",.9)),
            test_results=listOf(TestResultDto("test-1","FAIL")))
        var recordedId:String?=null
        compose.setContent {
            var session by remember {mutableStateOf(original)}
            var revision by remember {mutableIntStateOf(0)}
            MaterialTheme(colorScheme=AutomotiveDarkColors) {
                Surface {
                    Column(Modifier.verticalScroll(rememberScrollState())) {
                        AnalysisWorkspace(session,true,revision,onAnalyze={},onRecord={id,_ ->
                            recordedId=id
                            session=recalculated
                            revision++
                        })
                    }
                }
            }
        }
        compose.onNodeWithText("Tests (1)").performClick()
        compose.onNodeWithText("Record result").performScrollTo().performClick()
        compose.onAllNodesWithText("Recalculated diagnosis").onFirst().assertExists()
        compose.onNodeWithText("Diagnosis updated from the latest test result").assertExists()
        compose.onNodeWithText("Results (1)").assertExists()
        assertEquals("test-1",recordedId)
        compose.onNodeWithText("Tests (1)").performClick()
        compose.onNodeWithText("1  Injector follow-up").assertExists()
    }
}
