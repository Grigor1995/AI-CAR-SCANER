package com.aicarscaner.mobile.presentation

import android.content.Intent
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.aicarscaner.mobile.data.api.DiagnosticSessionDto
import com.aicarscaner.mobile.data.obd.LiveDataSnapshot

@Composable
internal fun DemoPanel(title: String, content: @Composable ColumnScope.() -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = androidx.compose.foundation.shape.RoundedCornerShape(16.dp),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = .45f)),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            if (title.isNotEmpty()) Text(title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            content()
        }
    }
}

@Composable
internal fun DemoHome(session: DiagnosticSessionDto, titles: List<String>, navigate: (Int) -> Unit) {
    DemoPanel(titles[6]) {
        session.vehicle?.let { VehicleModelArtwork(it.make, it.model, it.chassis.orEmpty()) }
        Text(session.vehicle?.let { "${it.make} ${it.model}" } ?: "—", style = MaterialTheme.typography.headlineSmall)
        Text(session.vehicle?.let { "${it.chassis.orEmpty()} • ${it.year ?: "—"} • ${it.engine.orEmpty()}" } ?: "—", color = MaterialTheme.colorScheme.onSurfaceVariant)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            DemoMetric("DTC", session.dtcs.size, Color(0xFFFF5D79), Modifier.weight(1f))
            DemoMetric(titles[8], session.test_results.size, Color(0xFF21D6A0), Modifier.weight(1f))
            DemoMetric(titles[4], session.hypotheses.size, Color(0xFFB67CFF), Modifier.weight(1f))
        }
    }
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedButton(onClick = { navigate(7) }, modifier = Modifier.weight(1f)) { Text("⚠ DTC") }
        OutlinedButton(onClick = { navigate(3) }, modifier = Modifier.weight(1f)) { Text("▥ ${titles[3]}") }
    }
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedButton(onClick = { navigate(8) }, modifier = Modifier.weight(1f)) { Text("✓ ${titles[8]}") }
        OutlinedButton(onClick = { navigate(4) }, modifier = Modifier.weight(1f)) { Text("◈ ${titles[4]}") }
    }
    DemoPanel(titles[8]) {
        val completed = session.test_results.filter { it.result == "PASS" || it.result == "FAIL" }.map { it.test_id }.toSet()
        val ids = session.recommendations.map { it.id }.toSet()
        val count = completed.intersect(ids).size
        LinearProgressIndicator(progress = { if (ids.isEmpty()) 0f else count.toFloat() / ids.size }, modifier = Modifier.fillMaxWidth())
        Text("$count/${ids.size}", style = MaterialTheme.typography.titleLarge)
        Button(onClick = { navigate(8) }, modifier = Modifier.fillMaxWidth()) { Text(titles[8]) }
    }
}

@Composable
private fun DemoMetric(title: String, count: Int, color: Color, modifier: Modifier) {
    Card(modifier = modifier, border = BorderStroke(1.dp, color.copy(alpha = .55f))) {
        Column(Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(count.toString(), color = color, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
            Text(title, style = MaterialTheme.typography.labelSmall)
        }
    }
}

@Composable
internal fun DemoDtcList(session: DiagnosticSessionDto, title: String) {
    Text(title, style = MaterialTheme.typography.headlineSmall)
    session.dtcs.forEach { code ->
        var expanded by remember(code.id) { mutableStateOf(false) }
        DemoPanel("⚠ ${code.code}") {
            Text(code.description ?: code.source ?: "—")
            OutlinedButton(onClick = { expanded = !expanded }) { Text(if (expanded) "−" else "+") }
            if (expanded) {
                session.evidence.filter { it.fact.contains(code.code, ignoreCase = true) }.forEach {
                    Text("${it.status} • ${it.fact}", style = MaterialTheme.typography.bodySmall)
                }
            }
        }
    }
    if (session.dtcs.isEmpty()) Text("—")
}

@Composable
internal fun DemoGuidedTests(session: DiagnosticSessionDto, title: String, record: (String, String) -> Unit) {
    Text(title, style = MaterialTheme.typography.headlineSmall)
    session.recommendations.forEach { test ->
        DemoPanel(test.title) {
            Text(test.purpose)
            test.prerequisites.forEach { Text("• $it") }
            test.safety_notes.forEach { Text(it, color = MaterialTheme.colorScheme.error) }
            Button(onClick = { record(test.id, test.title) }, modifier = Modifier.fillMaxWidth()) { Text("PASS / FAIL / INCOMPLETE") }
        }
    }
    session.test_results.forEach { result ->
        val color = when (result.result) { "PASS" -> Color(0xFF21D6A0); "FAIL" -> Color(0xFFFF5D79); else -> Color(0xFFFFC663) }
        DemoPanel(result.testName ?: result.test_id) { Text(result.result, color = color, fontWeight = FontWeight.Bold) }
    }
    if (session.recommendations.isEmpty()) Text("—")
}

@Composable
internal fun DemoLiveCharts(history: List<LiveDataSnapshot>) {
    val channels = listOf(
        Triple("RPM", history.mapNotNull { it.rpm }, Color(0xFF20B9FF)),
        Triple("Coolant °C", history.mapNotNull { it.coolantC }, Color(0xFFFF5D79)),
        Triple("MAP kPa", history.mapNotNull { it.mapKpa }, Color(0xFFB67CFF)),
        Triple("Speed km/h", history.mapNotNull { it.speedKph }, Color(0xFF21D6A0))
    )
    channels.forEach { (title, values, color) ->
        DemoPanel(title) {
            Text(values.lastOrNull()?.let { "%.1f".format(it) } ?: "—", style = MaterialTheme.typography.titleLarge, color = color)
            Canvas(Modifier.fillMaxWidth().height(85.dp)) {
                for (line in 1..3) drawLine(Color(0xFF20465D), Offset(0f, size.height * line / 4), Offset(size.width, size.height * line / 4))
                if (values.size >= 2) {
                    val min = values.minOrNull() ?: 0.0
                    val span = ((values.maxOrNull() ?: 0.0) - min).coerceAtLeast(.00001)
                    val path = Path()
                    values.forEachIndexed { index, value ->
                        val x = size.width * index / (values.size - 1)
                        val y = size.height * (1 - (value - min) / span).toFloat()
                        if (index == 0) path.moveTo(x, y) else path.lineTo(x, y)
                    }
                    drawPath(path, color, style = Stroke(width = 3f))
                }
            }
        }
    }
}

@Composable
internal fun DemoReports(session: DiagnosticSessionDto, title: String, shareLabel: String) {
    val context = LocalContext.current
    DemoPanel(title) {
        Text(session.vehicle?.let { "${it.make} ${it.model}" } ?: "—", style = MaterialTheme.typography.titleLarge)
        Text(session.session_id)
        Text("DTC: ${session.dtcs.size} • ${session.state}")
        Button(onClick = {
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "text/plain"
                putExtra(Intent.EXTRA_TEXT, com.google.gson.Gson().toJson(session))
            }
            context.startActivity(Intent.createChooser(intent, shareLabel))
        }, modifier = Modifier.fillMaxWidth()) { Text(shareLabel) }
        session.audit_log.takeLast(20).reversed().forEach { Text(it.event) }
    }
}

@Composable
internal fun DemoTeach(title: String, draftLabel: String, shareLabel: String) {
    val context = LocalContext.current
    val preferences = remember { context.getSharedPreferences("repair_notes", 0) }
    var note by remember { mutableStateOf(preferences.getString("draft", "").orEmpty()) }
    DemoPanel(title) {
        OutlinedTextField(value = note, onValueChange = {
            note = it
            preferences.edit().putString("draft", it).apply()
        }, modifier = Modifier.fillMaxWidth(), minLines = 8, label = { Text(draftLabel) })
        Button(onClick = {
            val intent = Intent(Intent.ACTION_SEND).apply { type = "text/plain"; putExtra(Intent.EXTRA_TEXT, note) }
            context.startActivity(Intent.createChooser(intent, shareLabel))
        }, enabled = note.isNotBlank(), modifier = Modifier.fillMaxWidth()) { Text(shareLabel) }
    }
}
