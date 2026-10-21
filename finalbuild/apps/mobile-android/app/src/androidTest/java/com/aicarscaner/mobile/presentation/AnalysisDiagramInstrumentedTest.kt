package com.aicarscaner.mobile.presentation
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.material3.*
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.aicarscaner.mobile.data.api.*
import com.aicarscaner.mobile.settings.AppLanguage
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
@RunWith(AndroidJUnit4::class)
class AnalysisDiagramInstrumentedTest {
 @get:Rule val compose=createAndroidComposeRule<TestHostActivity>()
 @Test fun translatedChartsUseLatestTestOutcomeAndUpdateScores(){
  var session by mutableStateOf(DiagnosticSessionDto("charts","TESTING",
   hypotheses=listOf(HypothesisDto("h1","ignition","Բոցավառման համակարգ",status="possible:0.65")),
   test_results=listOf(TestResultDto("t1","FAIL"),TestResultDto("t1","PASS"),TestResultDto("t2","INCOMPLETE"))))
  var language by mutableStateOf(AppLanguage.HY)
  var light by mutableStateOf(false)
  compose.setContent {CompositionLocalProvider(LocalDashboardLanguage provides language){MaterialTheme(colorScheme=if(light) AutomotiveLightColors else AutomotiveDarkColors){Surface(Modifier.fillMaxSize()){Column(Modifier.padding(16.dp)){AnalysisDiagram(session)}}}}}
  compose.onNodeWithText("65%",useUnmergedTree=true).assertExists()
  compose.runOnIdle {session=session.copy(hypotheses=listOf(HypothesisDto("h1","ignition","Բոցավառման համակարգ",status="supported_by_test:0.85")))}
  compose.onNodeWithText("85%",useUnmergedTree=true).assertExists()
  compose.onNodeWithText("Արդյունքներ").performClick()
  compose.onNodeWithContentDescription("Նորմալ: 1").assertExists()
  compose.onNodeWithContentDescription("Խնդիր կա: 0").assertExists()
  compose.onNodeWithContentDescription("Անավարտ: 1").assertExists()
  compose.runOnIdle {language=AppLanguage.RU;light=true}
  compose.onNodeWithContentDescription("Норма: 1").assertExists()
  compose.onNodeWithContentDescription("Есть проблема: 0").assertExists()
 }
}
