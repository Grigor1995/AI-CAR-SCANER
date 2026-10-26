package com.aicarscaner.mobile.settings

import android.content.Context

internal fun normalizeLauncherOrder(saved: List<Int>, defaults: List<Int>): List<Int> =
    saved.filter { it in defaults }.distinct() + defaults.filter { it !in saved }

internal fun moveLauncherItem(order: List<Int>, source: Int, target: Int): List<Int> {
    if(source == target || source !in order || target !in order) return order
    val index=order.indexOf(target)
    return order.toMutableList().apply { remove(source);add(index,source) }
}

/** A native presentation preference; it never changes backend workflow identifiers. */
internal class LauncherOrderStore(context: Context, name: String = "ai_car_launcher_layout") {
    private val prefs=context.applicationContext.getSharedPreferences(name,Context.MODE_PRIVATE)
    fun load(defaults: List<Int>): List<Int> {
        val raw=runCatching {prefs.getString("order","")}.getOrNull().orEmpty()
        return normalizeLauncherOrder(raw.split(',').mapNotNull { it.toIntOrNull() },defaults)
    }
    fun save(order: List<Int>) { prefs.edit().putString("order",order.joinToString(",")).apply() }
}
