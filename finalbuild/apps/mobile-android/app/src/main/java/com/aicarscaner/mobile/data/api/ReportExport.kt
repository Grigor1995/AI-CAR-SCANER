package com.aicarscaner.mobile.data.api

import com.google.gson.Gson
import com.google.gson.JsonElement

/** Export a copy; internal session routing/persistence keeps its original ID. */
internal fun diagnosticReportJson(session: DiagnosticSessionDto): String {
    val gson = Gson()
    val snapshot = gson.toJsonTree(session)
    fun removeSessionIds(value: JsonElement) {
        when {
            value.isJsonObject -> {
                value.asJsonObject.remove("session_id")
                value.asJsonObject.entrySet().forEach { removeSessionIds(it.value) }
            }
            value.isJsonArray -> value.asJsonArray.forEach { removeSessionIds(it) }
        }
    }
    removeSessionIds(snapshot)
    return gson.toJson(snapshot)
}
