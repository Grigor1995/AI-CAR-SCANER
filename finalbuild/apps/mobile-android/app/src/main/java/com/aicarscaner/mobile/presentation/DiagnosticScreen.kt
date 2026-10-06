package com.aicarscaner.mobile.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.aicarscaner.mobile.data.api.VehicleDto

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
    var dtc by remember { mutableStateOf("") }

    MaterialTheme {
        Column(
            modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text("AI CAR SCANER", style = MaterialTheme.typography.headlineMedium)
            Text("Diagnostic Session", style = MaterialTheme.typography.titleMedium)

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
                        VehicleDto(make, model, year.toIntOrNull(), engine, buildList { if (petrol) add("petrol"); if (lpg) add("LPG") })
                    )
                },
                enabled = !state.loading && state.session == null,
                modifier = Modifier.fillMaxWidth()
            ) { Text("Create Diagnostic Session") }

            state.session?.let { session ->
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("Session", style = MaterialTheme.typography.titleMedium)
                        Text(session.session_id)
                        Text("Analysis state: ${session.state}", style = MaterialTheme.typography.titleMedium)
                    }
                }

                OutlinedTextField(
                    symptom, { symptom = it }, Modifier.fillMaxWidth(),
                    label = { Text("Symptom") }
                )
                Button(
                    onClick = { viewModel.addSymptom(symptom) },
                    enabled = symptom.isNotBlank() && !state.loading,
                    modifier = Modifier.fillMaxWidth()
                ) { Text("Add Symptom") }

                OutlinedTextField(
                    dtc, { dtc = it }, Modifier.fillMaxWidth(),
                    label = { Text("DTC, e.g. P0302") }
                )
                Button(
                    onClick = { viewModel.addDtc(dtc) },
                    enabled = dtc.isNotBlank() && !state.loading,
                    modifier = Modifier.fillMaxWidth()
                ) { Text("Add DTC") }

                Button(
                    onClick = { viewModel.analyze() },
                    enabled = !state.loading,
                    modifier = Modifier.fillMaxWidth()
                ) { Text("Analyze") }

                if (session.hypotheses.isNotEmpty()) {
                    Text("Hypotheses", style = MaterialTheme.typography.titleLarge)
                    session.hypotheses.forEach { hypothesis ->
                        Card(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                Text(hypothesis.title, style = MaterialTheme.typography.titleMedium)
                                Text("Category: ${hypothesis.category}")
                                Text("Status: ${hypothesis.status}")
                                Text("Confidence / score: ${"%.2f".format(hypothesis.score)}")
                                Text("Rationale: ${hypothesis.rationale}")
                            }
                        }
                    }
                }

                if (session.recommendations.isNotEmpty()) {
                    Text("Recommendations", style = MaterialTheme.typography.titleLarge)
                    session.recommendations.forEach { recommendation ->
                        Card(Modifier.fillMaxWidth()) {
                            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                Text(recommendation.title, style = MaterialTheme.typography.titleMedium)
                                Text("Priority: ${recommendation.priority}")
                                Text("Purpose: ${recommendation.purpose}")
                                recommendation.expected_observation?.let { Text("Expected observation: $it") }
                            }
                        }
                    }
                }

                if (session.audit_log.isNotEmpty()) {
                    Text("Audit Events", style = MaterialTheme.typography.titleLarge)
                    session.audit_log.forEach { event ->
                        Text(buildString {
                            append(event.event)
                            event.hypotheses?.let { append(" (hypotheses: $it)") }
                        })
                    }
                }
            }

            if (state.loading) CircularProgressIndicator()
            state.error?.let { Text("Error: $it", color = MaterialTheme.colorScheme.error) }
        }
    }
}
