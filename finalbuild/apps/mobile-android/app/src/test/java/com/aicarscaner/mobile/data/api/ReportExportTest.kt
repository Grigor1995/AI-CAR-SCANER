package com.aicarscaner.mobile.data.api

import com.google.gson.JsonParser
import org.junit.Assert.*
import org.junit.Test

class ReportExportTest {
    @Test fun reportHidesInternalIdAndRetainsDiagnosticData() {
        val session = DiagnosticSessionDto("private-session-abcdef", "TESTING",
            dtcs = listOf(DtcDto("dtc-1", "P0302")))
        val report = diagnosticReportJson(session)
        val data = JsonParser.parseString(report).asJsonObject
        assertFalse(data.has("session_id"))
        assertFalse(report.contains(session.session_id))
        assertEquals("P0302", data["dtcs"].asJsonArray[0].asJsonObject["code"].asString)
        assertEquals("private-session-abcdef", session.session_id)
    }
}
