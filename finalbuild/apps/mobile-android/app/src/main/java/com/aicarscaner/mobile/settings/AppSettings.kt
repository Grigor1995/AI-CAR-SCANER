package com.aicarscaner.mobile.settings

import android.content.Context

enum class AppLanguage(val code: String) {
    EN("en"),
    RU("ru"),
    HY("hy")
}

data class AppSettings(
    val language: AppLanguage = AppLanguage.EN,
    val darkTheme: Boolean = true,
    val usUnits: Boolean = false,
    val analogDisplay: Boolean = true
)

class AppSettingsStore(context: Context) {
    private val prefs = context.getSharedPreferences("ai_car_scaner_settings", Context.MODE_PRIVATE)

    fun load(): AppSettings = AppSettings(
        language = runCatching {
            AppLanguage.valueOf(prefs.getString("language", AppLanguage.EN.name) ?: AppLanguage.EN.name)
        }.getOrDefault(AppLanguage.EN),
        darkTheme = prefs.getBoolean("dark_theme", true),
        usUnits = prefs.getBoolean("us_units", false),
        analogDisplay = prefs.getBoolean("analog_display", true)
    )

    fun save(settings: AppSettings) {
        prefs.edit()
            .putString("language", settings.language.name)
            .putBoolean("dark_theme", settings.darkTheme)
            .putBoolean("us_units", settings.usUnits)
            .putBoolean("analog_display", settings.analogDisplay)
            .apply()
    }
}