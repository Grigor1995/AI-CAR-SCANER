package com.aicarscaner.mobile.settings

import android.content.Context
import android.content.SharedPreferences
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify
import org.junit.Assert.assertEquals
import org.junit.Test

class AppSettingsStoreTest {
    private val context = mockk<Context>()
    private val preferences = mockk<SharedPreferences>()
    private val editor = mockk<SharedPreferences.Editor>()

    private fun store(): AppSettingsStore {
        every {
            context.getSharedPreferences("ai_car_scaner_settings", Context.MODE_PRIVATE)
        } returns preferences
        return AppSettingsStore(context)
    }

    @Test
    fun loadRestoresSavedLanguageAndTheme() {
        every { preferences.getString("language", "EN") } returns "RU"
        every { preferences.getBoolean("dark_theme", true) } returns false

        val settings = store().load()

        assertEquals(AppLanguage.RU, settings.language)
        assertEquals(false, settings.darkTheme)
    }

    @Test
    fun loadFallsBackToEnglishWhenSavedLanguageIsUnknown() {
        every { preferences.getString("language", "EN") } returns "FUTURE_LANGUAGE"
        every { preferences.getBoolean("dark_theme", true) } returns true

        val settings = store().load()

        assertEquals(AppLanguage.EN, settings.language)
        assertEquals(true, settings.darkTheme)
    }

    @Test
    fun loadUsesDefaultsWhenLanguagePreferenceIsNull() {
        every { preferences.getString("language", "EN") } returns null
        every { preferences.getBoolean("dark_theme", true) } returns true

        val settings = store().load()

        assertEquals(AppSettings(), settings)
    }

    @Test
    fun saveWritesLanguageAndThemeThenAppliesEditor() {
        every { preferences.edit() } returns editor
        every { editor.putString("language", "HY") } returns editor
        every { editor.putBoolean("dark_theme", false) } returns editor
        every { editor.apply() } returns Unit

        store().save(AppSettings(language = AppLanguage.HY, darkTheme = false))

        verify(exactly = 1) { preferences.edit() }
        verify(exactly = 1) { editor.putString("language", "HY") }
        verify(exactly = 1) { editor.putBoolean("dark_theme", false) }
        verify(exactly = 1) { editor.apply() }
    }
}
