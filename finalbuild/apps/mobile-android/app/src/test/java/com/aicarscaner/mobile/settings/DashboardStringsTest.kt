package com.aicarscaner.mobile.settings

import org.junit.Assert.*
import org.junit.Test

class DashboardStringsTest {
    @Test fun everyDashboardMessageHasBothTranslations() {
        dashboardTranslations.forEach { (english, _) ->
            listOf(AppLanguage.HY,AppLanguage.RU).forEach { language ->
                val translated=dashboardText(language,english)
                assertTrue("Missing $language: $english", translated.isNotBlank())
                assertNotEquals("English fallback for $language: $english",english,translated)
            }
            assertEquals(english,dashboardText(AppLanguage.EN,english))
        }
    }
    @Test fun diagnosticCodesUnitsAndUnknownValuesArePreserved() {
        listOf("P0302","RPM","kPa","Mercedes-Benz","Custom text").forEach { original ->
            assertEquals(original,dashboardText(AppLanguage.HY,original))
            assertEquals(original,dashboardText(AppLanguage.RU,original))
        }
        assertEquals("UNRECOGNIZED",localizedEvidenceSource(AppLanguage.HY,"UNRECOGNIZED"))
        assertNotEquals("ECU_REPORTED",localizedEvidenceSource(AppLanguage.HY,"ECU_REPORTED"))
    }
    @Test fun connectionStatusUpdatesLanguageWithoutChangingDeviceNames(){
        assertEquals(strings(AppLanguage.HY).notConnected,localizedConnectionStatus(AppLanguage.HY,"Not connected"))
        assertEquals(strings(AppLanguage.RU).notConnected,localizedConnectionStatus(AppLanguage.RU,strings(AppLanguage.HY).notConnected))
        assertEquals(strings(AppLanguage.HY).connected+": USB ELM327",localizedConnectionStatus(AppLanguage.HY,"Connected to USB ELM327"))
        assertEquals("P0302",localizedConnectionStatus(AppLanguage.HY,"P0302"))
    }
}
