package com.aicarscaner.mobile.presentation

import android.content.Context
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import com.aicarscaner.mobile.settings.LauncherOrderStore
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test

class LauncherReorderTest {
    @get:Rule val compose=createAndroidComposeRule<TestHostActivity>()

    @Test fun longPressDragPersistsAndTapStillOpensTheCorrectWorkflow() {
        val context=compose.activity
        val name="launcher-reorder-test"
        context.getSharedPreferences(name,Context.MODE_PRIVATE).edit().clear().commit()
        val store=LauncherOrderStore(context,name)
        var generation by mutableIntStateOf(0)
        var destination=-1
        compose.setContent {
            MaterialTheme(colorScheme=AutomotiveDarkColors) {
                Column(Modifier.verticalScroll(rememberScrollState())) {
                    key(generation) { DashboardSections(orderStore=store,navigate={destination=it}) }
                }
            }
        }
        val start=compose.onNodeWithText("Symptoms").fetchSemanticsNode().boundsInRoot.center
        val end=compose.onNodeWithText("Diagnostic").fetchSemanticsNode().boundsInRoot.center
        compose.onRoot().performTouchInput {
            down(start)
            advanceEventTime(700)
            moveTo(start)
            moveTo(end,500)
            up()
        }
        compose.runOnIdle {
            assertEquals(listOf(14,0),store.load(listOf(0,14,2,1,3,8,4,7,9,10,6,5,13,12)).take(2))
            assertEquals(-1,destination) // Dragging must not accidentally open a page.
            generation++
        }
        val diagnostic=compose.onNodeWithText("Diagnostic")
        val symptom=compose.onNodeWithText("Symptoms")
        assertTrue(diagnostic.fetchSemanticsNode().boundsInRoot.left < symptom.fetchSemanticsNode().boundsInRoot.left)
        diagnostic.performClick()
        compose.runOnIdle {assertEquals(14,destination)}
    }
}
