package com.aicarscaner.mobile.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.ScrollableTabRow
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.aicarscaner.mobile.data.api.VehicleDto
import kotlin.math.roundToInt

@Composable
fun DiagnosticScreen(viewModel: DiagnosticViewModel) {
    val state by viewModel.uiState.collectAsState()
    var make by remember { mutableStateOf("Mercedes") }
    var model by remember { mutableStateOf("W211") }
    var year by remember { mutableStateOf("2006") }
    var engine by remember { mutableStateOf("M272 3.5") }
    var petrol by remember { mutableStateOf(true) }
    var lpg by remember { mutableStateOf(true) }
    var symptom by remember { mutableStateOf("") }
    var editingSymptomId by remember { mutableStateOf<String?>(null) }
    var dtc by remember { mutableStateOf("") }
    var selectedTab by remember { mutableIntStateOf(0) }

    MaterialTheme {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text("AI CAR SCANER", style = MaterialTheme.typography.headlineMedium)
            Text("Diagnostic Session", style = MaterialTheme.typography.titleMedium)

            if (state.session == null) {
                OutlinedTextField(make, { make = it }, Modifier.fillMaxWidth(), label = { Text("Make") })
                OutlinedTextField(model, { model = it }, Modifier.fillMaxWidth(), label = { Text("Model") })
                OutlinedTextField(year, { year = it }, Modifier.fillMaxWidth(), label = { Text("Year") })
                OutlinedTextField(engine, { engine = it }, Modifier.fillMaxWidth(), label = { Text("Engine") })

                Text("Fuel", style = MaterialTheme.typography.titleMedium)
                Row {
                    Checkbox(checked = petrol, onCheckedChange = { petrol = it })
                    Text("Petrol")
                }
                Row {
                    Checkbox(checked = lpg, onCheckedChange = { lpg = it })
                    Text("LPG")
                }

                Button(
                    onClick = {
                        viewModel.createSession(
                            VehicleDto(
                                make,
                                model,
                                year.toIntOrNull(),
                                engine,
                                buildList {
                                    if (petrol) add("petrol")
                                    if (lpg) add("LPG")
                                }
                            )
                        )
                    },
                    enabled = !state.loading,
                    modifier = Modifier.fillMaxWidth()
                ) { Text("Create Diagnostic Session") }
            } else {
                val session = state.session!!
                val tabs = listOf(
                    "Overview",
                    "Symptoms (${session.symptoms.size})",
                    "DTC (${session.dtcs.size})",
                    "Analysis",
                    "Activity"
                )

                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("Session", style = MaterialTheme.typography.titleMedium)
                        Text(session.session_id)
                        Text("State: ${session.state}")
                    }
                }

                ScrollableTabRow(selectedTabIndex = selectedTab) {
                    tabs.forEachIndexed { index, title ->
                        Tab(
                            selected = selectedTab == index,
                            onClick = { selectedTab = index },
                            text = { Text(title) }
                        )
                    }
                }

                when (selectedTab) {
                    0 -> {
                        Text("Diagnostic overview", style = MaterialTheme.typography.titleLarge)
                        Text(
                            "Add symptoms and DTCs first, then run Analyze. " +
                                "The system keeps hypotheses evidence-based and avoids unsupported component verdicts."
                        )
                        if (session.recommendations.isNotEmpty()) {
                            Text("Next recommended test", style = MaterialTheme.typography.titleMedium)
                            session.recommendations.maxByOrNull { it.priority }?.let { recommendation ->
                                Card(Modifier.fillMaxWidth()) {
                                    Column(
                                        Modifier.padding(16.dp),
                                        verticalArrangement = Arrangement.spacedBy(6.dp)
                                    ) {
                                        Text(recommendation.title, style = MaterialTheme.typography.titleMedium)
                                        Text("Priority: ${(recommendation.priority * 100).roundToInt()}%")
                                        Text(recommendation.purpose)
                                    }
                                }
                            }
                        }
                    }

                    1 -> {
                        Text("Symptoms", style = MaterialTheme.typography.titleLarge)
                        Text(
                            "Describe what the driver observes. Include RPM, load, temperature, fuel mode, " +
                                "and when the symptom changes."
                        )

                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = {
                                symptom = "Engine shakes and hesitates when accelerating below 2000 RPM"
                            }) {
                                Text("Low RPM")
                            }
                            Button(onClick = { symptom = "Engine misfires under load" }) {
                                Text("Misfire")
                            }
                        }

                        OutlinedTextField(
                            value = symptom,
                            onValueChange = { symptom = it },
                            modifier = Modifier.fillMaxWidth(),
                            minLines = 4,
                            maxLines = 6,
                            label = { Text("Describe the symptom") },
                            placeholder = {
                                Text("Example: Smooth on petrol, shakes on LPG below 2000 RPM under load")
                            },
                            supportingText = { Text("${symptom.length}/500") }
                        )

                        if (editingSymptomId != null) {
                            Text("Editing symptom", style = MaterialTheme.typography.labelLarge)
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Button(
                                    onClick = {
                                        viewModel.updateSymptom(editingSymptomId!!, symptom.trim())
                                        editingSymptomId = null
                                    },
                                    enabled = symptom.trim().length >= 3 &&
                                        symptom.length <= 500 && !state.loading,
                                    modifier = Modifier.weight(1f)
                                ) { Text("Save Changes") }
                                Button(
                                    onClick = {
                                        editingSymptomId = null
                                        symptom = ""
                                    },
                                    enabled = !state.loading,
                                    modifier = Modifier.weight(1f)
                                ) { Text("Cancel") }
                            }
                        } else {
                            Button(
                                onClick = {
                                    viewModel.addSymptom(symptom.trim())
                                    symptom = ""
                                },
                                enabled = symptom.trim().length >= 3 &&
                                    symptom.length <= 500 && !state.loading,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("Add Symptom") }
                        }

                        session.symptoms.forEachIndexed { index, item ->
                            Card(Modifier.fillMaxWidth()) {
                                Column(
                                    Modifier.padding(16.dp),
                                    verticalArrangement = Arrangement.spacedBy(6.dp)
                                ) {
                                    Text("Symptom ${index + 1}", style = MaterialTheme.typography.labelLarge)
                                    Text(item.raw_text)
                                    item.normalized.takeIf { it.isNotEmpty() }?.let { normalized ->
                                        val formatted = normalized.entries.joinToString(", ") { entry ->
                                            "${entry.key}=${entry.value}"
                                        }
                                        Text(
                                            "Normalized: ${formatted}",
                                            style = MaterialTheme.typography.bodySmall
                                        )
                                    }
                                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                        Button(
                                            onClick = {
                                                symptom = item.raw_text
                                                editingSymptomId = item.id
                                            },
                                            enabled = !state.loading
                                        ) { Text("Edit") }
                                        Button(
                                            onClick = {
                                                viewModel.deleteSymptom(item.id)
                                                if (editingSymptomId == item.id) {
                                                    editingSymptomId = null
                                                    symptom = ""
                                                }
                                            },
                                            enabled = !state.loading
                                        ) { Text("Delete") }
                                    }
                                }
                            }
                        }
                    }

                    2 -> {
                        Text("Diagnostic Trouble Codes", style = MaterialTheme.typography.titleLarge)
                        OutlinedTextField(
                            dtc,
                            { dtc = it.uppercase() },
                            Modifier.fillMaxWidth(),
                            label = { Text("DTC, e.g. P0302") }
                        )
                        Button(
                            onClick = {
                                viewModel.addDtc(dtc.trim())
                                dtc = ""
                            },
                            enabled = dtc.trim().isNotEmpty() && !state.loading,
                            modifier = Modifier.fillMaxWidth()
                        ) { Text("Add DTC") }

                        if (session.dtcs.isEmpty()) {
                            Text("No DTCs recorded yet.")
                        } else {
                            session.dtcs.forEachIndexed { index, item ->
                                Card(Modifier.fillMaxWidth()) {
                                    Column(
                                        Modifier.padding(16.dp),
                                        verticalArrangement = Arrangement.spacedBy(4.dp)
                                    ) {
                                        Text("DTC ${index + 1}", style = MaterialTheme.typography.labelLarge)
                                        Text(item.code, style = MaterialTheme.typography.titleMedium)
                                        item.description?.let { Text(it) }
                                        item.source?.let {
                                            Text("Source: ${it}", style = MaterialTheme.typography.bodySmall)
                                        }
                                    }
                                }
                            }
                        }
                    }

                    3 -> {
                        Text("Analysis", style = MaterialTheme.typography.titleLarge)
                        Button(
                            onClick = { viewModel.analyze() },
                            enabled = !state.loading,
                            modifier = Modifier.fillMaxWidth()
                        ) { Text("Analyze Diagnostic Session") }

                        session.hypotheses.forEach { hypothesis ->
                            Card(Modifier.fillMaxWidth()) {
                                Column(
                                    Modifier.padding(16.dp),
                                    verticalArrangement = Arrangement.spacedBy(6.dp)
                                ) {
                                    Text(
                                        hypothesis.category,
                                        style = MaterialTheme.typography.titleMedium
                                    )
                                    Text("Status: ${hypothesis.status}")
                                    Text(hypothesis.statement)
                                }
                            }
                        }

                        if (session.recommendations.isNotEmpty()) {
                            Text("Recommended tests", style = MaterialTheme.typography.titleMedium)
                            session.recommendations.forEach { recommendation ->
                                Card(Modifier.fillMaxWidth()) {
                                    Column(
                                        Modifier.padding(16.dp),
                                        verticalArrangement = Arrangement.spacedBy(6.dp)
                                    ) {
                                        Text(
                                            recommendation.title,
                                            style = MaterialTheme.typography.titleMedium
                                        )
                                        Text(
                                            "Priority: ${(recommendation.priority * 100).roundToInt()}%"
                                        )
                                        Text("Purpose: ${recommendation.purpose}")
                                    }
                                }
                            }
                        }
                    }

                    4 -> {
                        Text("Activity", style = MaterialTheme.typography.titleLarge)
                        if (session.audit_log.isEmpty()) {
                            Text("No activity recorded yet.")
                        } else {
                            session.audit_log.forEach { event ->
                                Card(Modifier.fillMaxWidth()) {
                                    Column(Modifier.padding(12.dp)) {
                                        Text(
                                            event.event,
                                            style = MaterialTheme.typography.labelLarge
                                        )
                                        event.hypotheses?.let {
                                            Text(
                                                "Hypotheses: ${it}",
                                                style = MaterialTheme.typography.bodySmall
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            if (state.loading) CircularProgressIndicator()
            state.error?.let { Text("Error: ${it}", color = MaterialTheme.colorScheme.error) }
        }
    }
}
