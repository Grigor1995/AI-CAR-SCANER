package com.aicarscaner.mobile.presentation

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.aicarscaner.mobile.data.api.DiagnosticSessionDto

/** Tests, their results and the recalculated diagnosis share the active session. */
@Composable
internal fun AnalysisWorkspace(
    session: DiagnosticSessionDto,
    loading: Boolean,
    resultRevision: Int,
    onAnalyze: () -> Unit,
    onRecord: (String, String) -> Unit
) {
    BackendTools("decision",session)
    var section by remember(session.session_id) { mutableIntStateOf(0) }
    LaunchedEffect(session.session_id, resultRevision) {
        if (resultRevision > 0) section = 0
    }
    if (resultRevision > 0) {
        DemoPanel("") {
            Text(dashboardLabel("Diagnosis updated from the latest test result"),
                color=MaterialTheme.colorScheme.primary,fontWeight=FontWeight.SemiBold)
            session.test_results.lastOrNull()?.let { result ->
                val extra=com.aicarscaner.mobile.settings.strings(LocalDashboardLanguage.current).extra
                val outcome=when(result.result){"PASS"->extra.pass;"FAIL"->extra.fail;else->extra.incomplete}
                Text("${result.testName ?: result.test_id.take(8)} • $outcome",style=MaterialTheme.typography.bodySmall)
            }
        }
    }
    val labels=listOf(dashboardLabel("AI analysis"),
        "${dashboardLabel("Tests")} (${session.recommendations.size})",
        "${dashboardLabel("Results")} (${session.test_results.associateBy {it.test_id}.size})")
    Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(4.dp)) {
        labels.forEachIndexed { index,label ->
            FilterChip(modifier=Modifier.weight(1f),selected=section==index,onClick={section=index},label={Text(label,style=MaterialTheme.typography.labelMedium)})
        }
    }
    when(section) {
        0 -> {
            Button(onClick=onAnalyze,enabled=!loading,modifier=Modifier.fillMaxWidth()) {Text(dashboardLabel("Analyze session"))}
            if(session.recommendations.isNotEmpty()) {
                OutlinedButton(onClick={section=1},modifier=Modifier.fillMaxWidth()) {
                    Text("${dashboardLabel("Guided tests")} (${session.recommendations.size}) ›")
                }
            }
            AnalysisDiagram(session)
            DemoHypotheses(session)
        }
        1 -> DemoGuidedTests(session,dashboardLabel("Guided tests")) {id,title -> onRecord(id,title)}
        2 -> DemoProgress(session) {section=1}
    }
}
