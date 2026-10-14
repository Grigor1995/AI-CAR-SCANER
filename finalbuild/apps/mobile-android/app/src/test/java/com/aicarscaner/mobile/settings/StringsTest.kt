package com.aicarscaner.mobile.settings

import org.junit.Assert.assertEquals
import org.junit.Test

class StringsTest {
    @Test
    fun stringsProvideExpectedLanguageLabels() {
        assertEquals("Diagnose", strings(AppLanguage.EN).diagnose)
        assertEquals("Диагностика", strings(AppLanguage.RU).diagnose)
        assertEquals("Ախտորոշում", strings(AppLanguage.HY).diagnose)
        assertEquals("PASS", strings(AppLanguage.EN).extra.pass)
        assertEquals("ПРОЙДЕН", strings(AppLanguage.RU).extra.pass)
        assertEquals("ԱՆՑԱՎ", strings(AppLanguage.HY).extra.pass)
    }

    @Test
    fun localizedStatePreservesEnglishAndTranslatesKnownStates() {
        assertEquals("CREATED", localizedState(AppLanguage.EN, "CREATED"))
        assertEquals("Создана", localizedState(AppLanguage.RU, "CREATED"))
        assertEquals("Ստեղծված է", localizedState(AppLanguage.HY, "CREATED"))
        assertEquals("Причина найдена", localizedState(AppLanguage.RU, "ROOT_CAUSE_FOUND"))
        assertEquals("Պատճառը գտնված է", localizedState(AppLanguage.HY, "ROOT_CAUSE_FOUND"))
    }

    @Test
    fun localizedStateFallsBackToOriginalUnknownValue() {
        assertEquals("FUTURE_STATE", localizedState(AppLanguage.RU, "FUTURE_STATE"))
        assertEquals("FUTURE_STATE", localizedState(AppLanguage.HY, "FUTURE_STATE"))
        assertEquals(" custom-state ", localizedState(AppLanguage.RU, " custom-state "))
    }

    @Test
    fun evidenceStatusIsLocalizedForSupportedStatuses() {
        val ru = strings(AppLanguage.RU).extra
        val hy = strings(AppLanguage.HY).extra

        assertEquals(ru.reported, localizedEvidenceStatus(AppLanguage.RU, "reported", ru))
        assertEquals(ru.measured, localizedEvidenceStatus(AppLanguage.RU, "MEASURED", ru))
        assertEquals(hy.calculated, localizedEvidenceStatus(AppLanguage.HY, "Calculated", hy))
        assertEquals(hy.inferred, localizedEvidenceStatus(AppLanguage.HY, "inferred", hy))
        assertEquals(ru.confirmed, localizedEvidenceStatus(AppLanguage.RU, "confirmed", ru))
        assertEquals(hy.rejectedStatus, localizedEvidenceStatus(AppLanguage.HY, "rejected", hy))
    }

    @Test
    fun unknownEvidenceStatusFallsBackToOriginalText() {
        val extra = strings(AppLanguage.HY).extra
        assertEquals("pending-review", localizedEvidenceStatus(AppLanguage.HY, "pending-review", extra))
        assertEquals("pending-review", localizedEvidenceStatus(AppLanguage.HY, "pending-review", extra))
    }

    @Test
    fun languageAndSettingsDefaultsAreStable() {
        assertEquals("en", AppLanguage.EN.code)
        assertEquals("ru", AppLanguage.RU.code)
        assertEquals("hy", AppLanguage.HY.code)
        assertEquals(AppLanguage.EN, AppSettings().language)
        assertEquals(true, AppSettings().darkTheme)
        assertEquals(false, AppSettings(darkTheme = false).darkTheme)
    }
}
