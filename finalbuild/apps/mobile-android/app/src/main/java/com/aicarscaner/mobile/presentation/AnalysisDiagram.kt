package com.aicarscaner.mobile.presentation

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.aicarscaner.mobile.data.api.DiagnosticSessionDto
import com.aicarscaner.mobile.data.api.TestResultDto
import com.aicarscaner.mobile.settings.strings
import kotlin.math.roundToInt

internal fun diagramEvidenceScore(status: String): Double? {
    val parts = status.split(':')
    if (parts.size != 2) return null
    return parts[1].toDoubleOrNull()?.takeIf { it.isFinite() && it in 0.0..1.0 }
}

internal fun diagramResultCounts(results: List<TestResultDto>): Map<String, Int> {
    val latest = results.associateBy { it.test_id }.values
    return listOf("PASS", "FAIL", "INCOMPLETE").associateWith { code ->
        latest.count { it.result.uppercase() == code }
    }
}

@Composable
internal fun AnalysisDiagram(session: DiagnosticSessionDto) {
    var showResults by remember(session.session_id) { mutableStateOf(false) }
    val extra = strings(LocalDashboardLanguage.current).extra
    DemoPanel(dashboardLabel("Diagram")) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            FilterChip(selected = !showResults, onClick = { showResults = false },
                modifier = Modifier.weight(1f), label = { Text(extra.hypotheses) })
            FilterChip(selected = showResults, onClick = { showResults = true },
                modifier = Modifier.weight(1f), label = { Text(dashboardLabel("Results")) })
        }
        if (showResults) {
            val counts = diagramResultCounts(session.test_results)
            if (session.test_results.isEmpty()) {
                Text(dashboardLabel("No test results yet"), color = MaterialTheme.colorScheme.onSurfaceVariant)
            } else {
                val maximum = counts.values.maxOrNull()?.coerceAtLeast(1) ?: 1
                counts.forEach { (code, count) ->
                    val label = when (code) { "PASS" -> extra.pass; "FAIL" -> extra.fail; else -> extra.incomplete }
                    val color = when (code) { "PASS" -> Color(0xFF21B98A); "FAIL" -> Color(0xFFEF526D); else -> Color(0xFFE5AF35) }
                    DiagramBar(label, count.toString(), count.toFloat() / maximum, color)
                }
                DiagramAxis(maximum.toString())
            }
        } else {
            val scores = session.hypotheses.mapNotNull { hypothesis ->
                diagramEvidenceScore(hypothesis.status)?.let { hypothesis to it }
            }
            if (scores.isEmpty()) {
                Text(dashboardLabel("Analyze the session to get scored hypotheses."), color = MaterialTheme.colorScheme.onSurfaceVariant)
            } else {
                scores.forEach { (hypothesis, score) ->
                    DiagramBar(hypothesis.statement, "${(score * 100).roundToInt()}%", score.toFloat(), MaterialTheme.colorScheme.primary)
                }
                DiagramAxis("100%")
                Text(dashboardLabel("Scores describe supporting evidence, not confirmed failures."),
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

@Composable
private fun DiagramBar(label: String, value: String, fraction: Float, color: Color) {
    val track = MaterialTheme.colorScheme.onSurface.copy(alpha = .06f)
    val grid = MaterialTheme.colorScheme.onSurface.copy(alpha = .12f)
    Column(Modifier.fillMaxWidth().semantics(mergeDescendants = true) { contentDescription = "$label: $value" },
        verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(label, Modifier.weight(1f), style = MaterialTheme.typography.bodySmall)
            Text(value, color = color, style = MaterialTheme.typography.labelLarge)
        }
        Canvas(Modifier.fillMaxWidth().height(28.dp)) {
            drawRoundRect(track, cornerRadius = CornerRadius(5.dp.toPx()))
            for (tick in 1..3) {
                val x = size.width * tick / 4
                drawLine(grid, Offset(x, 0f), Offset(x, size.height), strokeWidth = 1.dp.toPx())
            }
            if (fraction > 0f) drawRoundRect(color, size = Size(size.width * fraction.coerceIn(0f, 1f), size.height),
                cornerRadius = CornerRadius(5.dp.toPx()))
        }
    }
}

@Composable
private fun DiagramAxis(maximum: String) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text("0", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(maximum, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}
