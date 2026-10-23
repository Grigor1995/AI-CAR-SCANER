package com.aicarscaner.mobile.presentation

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import com.aicarscaner.mobile.settings.AppLanguage
import com.aicarscaner.mobile.settings.dashboardText
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class DesktopLauncherTest {
    @get:Rule val compose=createAndroidComposeRule<TestHostActivity>()

    @Test fun localizedLauncherKeepsSymptomsDiagnosticsAndAdapterDistinct() {
        var destination=-1
        compose.setContent {
            CompositionLocalProvider(LocalDashboardLanguage provides AppLanguage.HY) {
                MaterialTheme(colorScheme=AutomotiveDarkColors) {
                    Column(Modifier.verticalScroll(rememberScrollState())) {
                        DashboardSections {destination=it}
                    }
                }
            }
        }
        for((label,id) in listOf("Symptoms" to 0,"Diagnostic" to 14,"VCI / Devices" to 2,"Vehicles" to 1,"Live Data" to 3)) {
            compose.onNodeWithText(dashboardText(AppLanguage.HY,label)).performScrollTo().performClick()
            compose.runOnIdle {assertEquals(id,destination)}
        }
        compose.onNodeWithText("⚙").assertDoesNotExist()
    }
}
