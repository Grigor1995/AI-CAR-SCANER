package com.aicarscaner.mobile.presentation

import android.Manifest
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothManager
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.aicarscaner.mobile.data.api.VehicleDto
import com.aicarscaner.mobile.data.obd.BluetoothObdClient
import kotlin.math.roundToInt
import kotlinx.coroutines.launch

private val AppDarkColors = darkColorScheme()

@Composable
fun DiagnosticScreen(viewModel: DiagnosticViewModel) {
    val state by viewModel.uiState.collectAsState()
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val obdClient = remember { BluetoothObdClient() }

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
    var editingVehicle by remember { mutableStateOf(false) }
    var obdDevices by remember { mutableStateOf<List<BluetoothDevice>>(emptyList()) }
    var obdStatus by remember { mutableStateOf("Not connected") }
    var obdResponse by remember { mutableStateOf("") }

    val bluetoothPermission = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        arrayOf(
            Manifest.permission.BLUETOOTH_CONNECT,
            Manifest.permission.BLUETOOTH_SCAN
        )
    } else {
        emptyArray()
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S ||
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.BLUETOOTH_CONNECT
            ) == PackageManager.PERMISSION_GRANTED
        ) {
            val adapter = context.getSystemService(BluetoothManager::class.java)?.adapter
            if (adapter != null) {
                obdDevices = adapter.bondedDevices.toList().sortedBy { it.name ?: it.address }
            }
        }
    }

    fun refreshObdDevices() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.BLUETOOTH_CONNECT
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            permissionLauncher.launch(bluetoothPermission)
            return
        }
        val adapter = context.getSystemService(BluetoothManager::class.java)?.adapter
        obdDevices = adapter?.bondedDevices?.toList()?.sortedBy { it.name ?: it.address } ?: emptyList()
    }

    LaunchedEffect(Unit) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.BLUETOOTH_CONNECT
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            permissionLauncher.launch(bluetoothPermission)
        } else {
            refreshObdDevices()
        }
    }

    DisposableEffect(Unit) {
        onDispose { obdClient.close() }
    }

    MaterialTheme(colorScheme = AppDarkColors) {
        Surface(modifier = Modifier.fillMaxSize()) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Column {
                        Text("AI CAR SCANER", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold)
                        state.session?.let { Text("Session ${it.session_id.take(8)}…", style = MaterialTheme.typography.bodySmall) }
                    }
                    if (state.session != null) {
                        Button(onClick = {
                            viewModel.clearSession()
                            selectedTab = 0
                            editingVehicle = false
                            symptom = ""
                            dtc = ""
                        }, enabled = !state.loading) {
                            Text("New")
                        }
                    }
                }

                if (state.session == null) {
                    Text("New diagnostic session", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Medium)
                    VehicleFields(
                        make, { make = it }, model, { model = it }, year, { year = it },
                        engine, { engine = it }, petrol, { petrol = it }, lpg, { lpg = it }
                    )
                    Button(
                        onClick = {
                            viewModel.createSession(
                                VehicleDto(make, model, year.toIntOrNull(), engine, buildList {
                                    if (petrol) add("petrol")
                                    if (lpg) add("LPG")
                                })
                            )
                        },
                        enabled = !state.loading,
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("Create Diagnostic Session") }
                } else {
                    val session = state.session!!
                    LaunchedEffect(session.vehicle) {
                        session.vehicle?.let { vehicle ->
                            make = vehicle.make
                            model = vehicle.model
                            year = vehicle.year?.toString().orEmpty()
                            engine = vehicle.engine.orEmpty()
                            petrol = vehicle.fuel.any { it.equals("petrol", true) }
                            lpg = vehicle.fuel.any { it.equals("lpg", true) }
                        }
                    }

                    val tabs = listOf(
                        "Diagnose ${session.symptoms.size + session.dtcs.size}",
                        "Session",
                        "OBD",
                        "Analysis",
                        "Activity"
                    )

                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            Text("Current session", style = MaterialTheme.typography.labelLarge)
                            Text(session.vehicle?.let { "${it.make} ${it.model}" } ?: "Vehicle not identified")
                            Text("State: ${session.state}", style = MaterialTheme.typography.bodySmall)
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
                            Text("Symptoms", style = MaterialTheme.typography.titleLarge)
                            OutlinedTextField(
                                value = symptom,
                                onValueChange = { symptom = it },
                                modifier = Modifier.fillMaxWidth(),
                                minLines = 3,
                                maxLines = 5,
                                label = { Text("Driver symptom") },
                                placeholder = { Text("Example: Shakes on LPG below 2000 RPM under load; petrol is normal") },
                                supportingText = { Text("${symptom.length}/500") }
                            )

                            if (editingSymptomId != null) {
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    Button(
                                        onClick = {
                                            viewModel.updateSymptom(editingSymptomId!!, symptom.trim())
                                            editingSymptomId = null
                                        },
                                        enabled = symptom.trim().length >= 3 && symptom.length <= 500 && !state.loading,
                                        modifier = Modifier.weight(1f)
                                    ) { Text("Save") }
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
                                    enabled = symptom.trim().length >= 3 && symptom.length <= 500 && !state.loading,
                                    modifier = Modifier.fillMaxWidth()
                                ) { Text("Add Symptom") }
                            }

                            session.symptoms.forEachIndexed { index, item ->
                                Card(Modifier.fillMaxWidth()) {
                                    Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                                        Text("Symptom ${index + 1}", style = MaterialTheme.typography.labelLarge)
                                        Text(item.raw_text)
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

                            Text("DTC", style = MaterialTheme.typography.titleLarge)
                            OutlinedTextField(
                                dtc,
                                { dtc = it.uppercase() },
                                Modifier.fillMaxWidth(),
                                label = { Text("Diagnostic trouble code") },
                                placeholder = { Text("P0302") }
                            )
                            Button(
                                onClick = {
                                    viewModel.addDtc(dtc.trim())
                                    dtc = ""
                                },
                                enabled = dtc.trim().isNotEmpty() && !state.loading,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("Add DTC") }

                            session.dtcs.forEach { item ->
                                Card(Modifier.fillMaxWidth()) {
                                    Column(Modifier.padding(12.dp)) {
                                        Text(item.code, style = MaterialTheme.typography.titleMedium)
                                        item.description?.let { Text(it) }
                                    }
                                }
                            }

                            Button(
                                onClick = { selectedTab = 3 },
                                enabled = !state.loading,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("Review Analysis") }
                        }

                        1 -> {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text("Current session", style = MaterialTheme.typography.titleLarge)
                                Button(onClick = { editingVehicle = !editingVehicle }, enabled = !state.loading) {
                                    Text(if (editingVehicle) "Cancel" else "Edit")
                                }
                            }

                            if (editingVehicle) {
                                VehicleFields(
                                    make, { make = it }, model, { model = it }, year, { year = it },
                                    engine, { engine = it }, petrol, { petrol = it }, lpg, { lpg = it }
                                )
                                Button(
                                    onClick = {
                                        viewModel.updateVehicle(
                                            VehicleDto(make, model, year.toIntOrNull(), engine, buildList {
                                                if (petrol) add("petrol")
                                                if (lpg) add("LPG")
                                            })
                                        )
                                        editingVehicle = false
                                    },
                                    enabled = !state.loading,
                                    modifier = Modifier.fillMaxWidth()
                                ) { Text("Save Session") }
                            } else {
                                Card(Modifier.fillMaxWidth()) {
                                    Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                                        Text("Vehicle", style = MaterialTheme.typography.labelLarge)
                                        Text("${session.vehicle?.make.orEmpty()} ${session.vehicle?.model.orEmpty()}")
                                        Text("Year: ${session.vehicle?.year ?: "—"}")
                                        Text("Engine: ${session.vehicle?.engine ?: "—"}")
                                        Text("Fuel: ${session.vehicle?.fuel?.joinToString(" + ").orEmpty()}")
                                        Text("ECU: ${session.vehicle?.ecu ?: "—"}")
                                    }
                                }
                            }

                            Button(
                                onClick = {
                                    viewModel.clearSession()
                                    selectedTab = 0
                                },
                                enabled = !state.loading,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("Start New Session") }
                        }

                        2 -> {
                            Text("OBD Connection", style = MaterialTheme.typography.titleLarge)
                            Text("Connect a paired Bluetooth ELM327-style adapter using a real Bluetooth SPP connection.")
                            Text("Status: ${obdStatus}", fontWeight = FontWeight.Medium)

                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Button(onClick = { refreshObdDevices() }) { Text("Refresh") }
                                Button(onClick = {
                                    context.startActivity(Intent(Settings.ACTION_BLUETOOTH_SETTINGS))
                                }) { Text("Bluetooth Settings") }
                            }

                            if (obdDevices.isEmpty()) {
                                Text("No paired Bluetooth devices. Pair the OBD adapter in Android settings first.")
                            } else {
                                obdDevices.forEach { device ->
                                    Card(Modifier.fillMaxWidth()) {
                                        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                                            Text(device.name ?: "Bluetooth device", style = MaterialTheme.typography.titleMedium)
                                            Text(device.address, style = MaterialTheme.typography.bodySmall)
                                            Button(
                                                onClick = {
                                                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
                                                        ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED
                                                    ) {
                                                        permissionLauncher.launch(bluetoothPermission)
                                                    } else {
                                                        scope.launch {
                                                            obdStatus = "Connecting…"
                                                            obdClient.connect(device)
                                                                .onSuccess { obdStatus = it }
                                                                .onFailure { obdStatus = "Connection failed: ${it.message ?: "unknown error"}" }
                                                        }
                                                    }
                                                },
                                                enabled = !state.loading
                                            ) { Text("Connect OBD") }
                                        }
                                    }
                                }
                            }

                            if (obdClient.isConnected) {
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    Button(onClick = {
                                        scope.launch {
                                            obdClient.readPid010c()
                                                .onSuccess { obdResponse = "RPM response: ${it}" }
                                                .onFailure { obdResponse = "RPM read failed: ${it.message}" }
                                        }
                                    }) { Text("Read RPM") }
                                    Button(onClick = {
                                        scope.launch {
                                            obdClient.readDtcs()
                                                .onSuccess { obdResponse = "DTC response: ${it}" }
                                                .onFailure { obdResponse = "DTC read failed: ${it.message}" }
                                        }
                                    }) { Text("Read DTCs") }
                                    Button(onClick = {
                                        obdClient.close()
                                        obdStatus = "Not connected"
                                        obdResponse = ""
                                    }) { Text("Disconnect") }
                                }
                            }

                            if (obdResponse.isNotBlank()) {
                                Card(Modifier.fillMaxWidth()) {
                                    Column(Modifier.padding(12.dp)) {
                                        Text("Adapter response", style = MaterialTheme.typography.labelLarge)
                                        Text(obdResponse)
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
                                    Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                                        Text(hypothesis.category, style = MaterialTheme.typography.titleMedium)
                                        Text("Status: ${hypothesis.status}")
                                        Text(hypothesis.statement)
                                    }
                                }
                            }

                            if (session.recommendations.isNotEmpty()) {
                                Text("Recommended tests", style = MaterialTheme.typography.titleMedium)
                                session.recommendations.forEach { recommendation ->
                                    Card(Modifier.fillMaxWidth()) {
                                        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                                            Text(recommendation.title, style = MaterialTheme.typography.titleMedium)
                                            Text("Priority: ${(recommendation.priority * 100).roundToInt()}%")
                                            Text(recommendation.purpose)
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
                                            Text(event.event, style = MaterialTheme.typography.labelLarge)
                                            event.hypotheses?.let { Text("Hypotheses: ${it}", style = MaterialTheme.typography.bodySmall) }
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

@Composable
private fun VehicleFields(
    make: String,
    onMake: (String) -> Unit,
    model: String,
    onModel: (String) -> Unit,
    year: String,
    onYear: (String) -> Unit,
    engine: String,
    onEngine: (String) -> Unit,
    petrol: Boolean,
    onPetrol: (Boolean) -> Unit,
    lpg: Boolean,
    onLpg: (Boolean) -> Unit
) {
    OutlinedTextField(make, onMake, Modifier.fillMaxWidth(), label = { Text("Make") })
    OutlinedTextField(model, onModel, Modifier.fillMaxWidth(), label = { Text("Model") })
    OutlinedTextField(year, onYear, Modifier.fillMaxWidth(), label = { Text("Year") })
    OutlinedTextField(engine, onEngine, Modifier.fillMaxWidth(), label = { Text("Engine") })

    Text("Fuel", style = MaterialTheme.typography.titleMedium)
    Row {
        Checkbox(checked = petrol, onCheckedChange = onPetrol)
        Text("Petrol")
    }
    Row {
        Checkbox(checked = lpg, onCheckedChange = onLpg)
        Text("LPG")
    }
}