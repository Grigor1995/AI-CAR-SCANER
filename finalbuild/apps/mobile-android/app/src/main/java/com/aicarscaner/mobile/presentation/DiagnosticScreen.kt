package com.aicarscaner.mobile.presentation

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
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
    var symptom by remember { mutableStateOf("") }
    var dtc by remember { mutableStateOf("") }

    MaterialTheme {
        Column(
            modifier = Modifier.fillMaxSize().padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text("AI CAR SCANER", style = MaterialTheme.typography.headlineMedium)
            Text("Diagnostic Session", style = MaterialTheme.typography.titleMedium)
            OutlinedTextField(make, { make = it }, Modifier.fillMaxWidth(), label = { Text("Make") })
            OutlinedTextField(model, { model = it }, Modifier.fillMaxWidth(), label = { Text("Model") })
            OutlinedTextField(year, { year = it }, Modifier.fillMaxWidth(), label = { Text("Year") })
            OutlinedTextField(engine, { engine = it }, Modifier.fillMaxWidth(), label = { Text("Engine") })

            Button(
                onClick = {
                    viewModel.createSession(
                        VehicleDto(make, model, year.toIntOrNull(), engine, listOf("petrol", "LPG"))
                    )
                },
                enabled = !state.loading && state.session == null,
                modifier = Modifier.fillMaxWidth()
            ) { Text("Create Diagnostic Session") }

            state.session?.let { session ->
                Text("Session: ${session.session_id}")
                Text("State: ${session.state}")
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
            }

            if (state.loading) CircularProgressIndicator()
            state.error?.let { Text("Error: $it", color = MaterialTheme.colorScheme.error) }
        }
    }
}
