package com.aicarscaner.mobile.presentation
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.material3.*
import androidx.compose.foundation.layout.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.aicarscaner.mobile.data.api.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
@RunWith(AndroidJUnit4::class)
class SessionPrivacyInstrumentedTest {
 @get:Rule val compose=createAndroidComposeRule<TestHostActivity>()
 @Test fun reportKeepsSessionIdentifierPrivate(){
  val session=DiagnosticSessionDto("private-session-abcdef","TESTING",vehicle=VehicleDto("Mercedes-Benz","E-Class","W211",2006),dtcs=listOf(DtcDto("dtc-1","P0302")))
  compose.setContent {MaterialTheme(colorScheme=AutomotiveDarkColors){Surface(Modifier.fillMaxSize()){Column(Modifier.padding(16.dp)){DemoReports(session,"Diagnostic report","Share report")}}}}
  compose.onAllNodesWithText(session.session_id,substring=true).assertCountEquals(0)
  compose.onAllNodesWithText(session.session_id.take(8),substring=true).assertCountEquals(0)
  compose.onNodeWithText("Mercedes-Benz E-Class").assertExists()
 }
}
