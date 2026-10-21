package com.aicarscaner.mobile.presentation

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.ui.Modifier
import com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.graphics.asAndroidBitmap
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.aicarscaner.mobile.settings.*
import org.junit.Assert.*
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class VehicleUiRegressionTest {
    @get:Rule val compose=createAndroidComposeRule<TestHostActivity>()

    @Test fun changingVehicleReplacesAnAlreadyLoadedPortrait() {
        var toyota by mutableStateOf(false)
        compose.setContent {
            MaterialTheme(colorScheme=AutomotiveDarkColors) {
                Column {
                    VehicleModelArtwork(
                        if(toyota) "Toyota" else "Mercedes-Benz",
                        if(toyota) "Corolla" else "E-Class",
                        if(toyota) "E140/E150" else "W211")
                    Button(onClick={toyota=!toyota}) {Text("Switch vehicle")}
                }
            }
        }
        val mercedes="Mercedes-Benz E-Class W211"
        val corolla="Toyota Corolla E140/E150"
        compose.waitUntil(5000) {compose.onAllNodesWithContentDescription(mercedes).fetchSemanticsNodes().isNotEmpty()}
        val before=compose.onNodeWithContentDescription(mercedes).captureToImage().asAndroidBitmap()
        compose.onNodeWithText("Switch vehicle").performClick()
        compose.waitUntil(5000) {compose.onAllNodesWithContentDescription(corolla).fetchSemanticsNodes().isNotEmpty()}
        val after=compose.onNodeWithContentDescription(corolla).captureToImage().asAndroidBitmap()
        assertFalse("Changing make/model must change the rendered image",before.sameAs(after))
    }

    @Test fun toolbarMakesSymptomsAndAnalysisReachableWithoutMore() {
        var symptoms=0
        var analyses=0
        compose.setContent {
            CompositionLocalProvider(LocalDashboardLanguage provides AppLanguage.HY) {
                MaterialTheme(colorScheme=AutomotiveDarkColors) {
                    Column {
                        DashboardToolbar("AI CAR SCANNER",true,false,false,
                            onHome={},onSettings={},onNewSession={},
                            onSymptoms={symptoms++},onAnalyze={analyses++})
                    }
                }
            }
        }
        compose.onNodeWithText(strings(AppLanguage.HY).symptoms).performClick()
        compose.onNodeWithText(dashboardText(AppLanguage.HY,"Analyze session")).performClick()
        assertEquals(1,symptoms)
        assertEquals(1,analyses)
    }

    @Test fun pickerHasOnePortraitOnlyAfterExplicitModelSelection() {
        compose.setContent {
            MaterialTheme(colorScheme=AutomotiveDarkColors) {
                Surface {
                    Column(Modifier.verticalScroll(rememberScrollState())) {
                        var make by remember { mutableStateOf("Mercedes-Benz") }
                        var model by remember { mutableStateOf("E-Class") }
                        val catalog=listOf(
                            VehicleCatalogEntryDto("Mercedes-Benz","E-Class","W211",2006,"M272","ME9.7"),
                            VehicleCatalogEntryDto("BMW","3-Series","E90",2007,"N52","MSV70"))
                        val selected=catalog.first {it.make==make && it.model==model}
                        VehicleFields(
                            text=strings(AppLanguage.EN),catalog=catalog,
                            make=make,onMake={make=it;model=if(it=="BMW") "3-Series" else "E-Class"},
                            model=model,onModel={model=it},chassis=selected.chassis.orEmpty(),onChassis={},
                            year=selected.year.toString(),onYear={},engine=selected.engine,onEngine={},
                            ecu=selected.ecu.orEmpty(),onEcu={},petrol=true,onPetrol={},lpg=false,onLpg={})
                    }
                }
            }
        }
        compose.onAllNodesWithContentDescription("Mercedes-Benz E-Class W211").assertCountEquals(0)
        compose.onAllNodesWithText("Mercedes-Benz").assertCountEquals(1)
        compose.onAllNodesWithText("E-Class").assertCountEquals(1)
        compose.onNodeWithText("Model").performScrollTo().performClick()
        compose.onAllNodesWithText("E-Class").onLast().performClick()
        compose.waitUntil(5000) {compose.onAllNodesWithContentDescription("Mercedes-Benz E-Class W211").fetchSemanticsNodes().size==1}
        compose.onNodeWithText("Make").performScrollTo().performClick()
        compose.onNodeWithText("BMW").performClick()
        compose.onAllNodesWithContentDescription("Mercedes-Benz E-Class W211").assertCountEquals(0)
        compose.onAllNodesWithContentDescription("BMW 3-Series E90").assertCountEquals(0)
        compose.onNodeWithText("Model").performScrollTo().performClick()
        compose.onAllNodesWithText("3-Series").onLast().performClick()
        compose.waitUntil(5000) {compose.onAllNodesWithContentDescription("BMW 3-Series E90").fetchSemanticsNodes().size==1}
    }
}
