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
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.Surface
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.TextButton
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
import com.aicarscaner.mobile.data.obd.UsbObdClient
import com.aicarscaner.mobile.data.obd.WifiObdClient
import com.aicarscaner.mobile.settings.AppLanguage
import com.aicarscaner.mobile.settings.AppSettings
import com.aicarscaner.mobile.settings.AppSettingsStore
import com.aicarscaner.mobile.settings.strings
import android.app.PendingIntent
import android.hardware.usb.UsbDevice
import android.hardware.usb.UsbManager
import kotlin.math.roundToInt
import kotlinx.coroutines.launch


@Composable
fun DiagnosticScreen(viewModel: DiagnosticViewModel) {
    val state by viewModel.uiState.collectAsState()
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val settingsStore = remember { AppSettingsStore(context) }
    var appSettings by remember { mutableStateOf(settingsStore.load()) }
    var settingsOpen by remember { mutableStateOf(false) }
    val text = strings(appSettings.language)

    val bluetoothClient = remember { BluetoothObdClient() }
    val wifiClient = remember { WifiObdClient() }
    val usbClient = remember { UsbObdClient() }

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
    var usbDevices by remember { mutableStateOf<List<UsbDevice>>(emptyList()) }
    var wifiHost by remember { mutableStateOf("") }
    var wifiPort by remember { mutableStateOf("35000") }
    var obdStatus by remember { mutableStateOf(text.notConnected) }
    var obdResponse by remember { mutableStateOf("") }
    var obdTransport by remember { mutableStateOf("bluetooth") }

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
            obdDevices = adapter?.bondedDevices?.toList()?.sortedBy {
                it.name ?: it.address
            } ?: emptyList()
        }
        refreshUsbDevices()
    }

    fun refreshBluetoothDevices() {
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
        obdDevices = adapter?.bondedDevices?.toList()?.sortedBy {
            it.name ?: it.address
        } ?: emptyList()
    }

    fun refreshUsbDevices() {
        val manager = context.getSystemService(UsbManager::class.java)
        usbDevices = manager?.deviceList?.values?.toList() ?: emptyList()
    }

    fun closeAllObd() {
        bluetoothClient.close()
        wifiClient.close()
        usbClient.close()
        obdStatus = text.notConnected
        obdResponse = ""
    }

    fun resetForNewSession() {
        viewModel.clearSession()
        selectedTab = 0
        editingVehicle = false
        editingSymptomId = null
        symptom = ""
        dtc = ""
        make = "Mercedes"
        model = "W211"
        year = "2006"
        engine = "M272 3.5"
        petrol = true
        lpg = true
    }

    LaunchedEffect(Unit) {
        refreshBluetoothDevices()
        refreshUsbDevices()
    }

    DisposableEffect(Unit) {
        onDispose {
            bluetoothClient.close()
            wifiClient.close()
            usbClient.close()
        }
    }

    if (settingsOpen) {
        SettingsDialog(
            settings = appSettings,
            text = text,
            onSettingsChanged = {
                appSettings = it
                settingsStore.save(it)
            },
            onClose = { settingsOpen = false }
        )
    }

    MaterialTheme(
        colorScheme = if (appSettings.darkTheme) darkColorScheme() else lightColorScheme()
    ) {
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
                        Text(text.appName, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold)
                        state.session?.let { Text("Session ${it.session_id.take(8)}…", style = MaterialTheme.typography.bodySmall) }
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        OutlinedButton(onClick = { settingsOpen = true }) {
                            Text(text.settings)
                        }
                        if (state.session != null) {
                            Button(onClick = { resetForNewSession() }, enabled = !state.loading) {
                                Text(text.newSession)
                            }
                        }
                    }
                }

                if (state.session == null) {
                    Text(text.newSession, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Medium)
                    VehicleFields(
                        text,
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
                    ) { Text(text.createSession) }
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
                        "${text.diagnose} (${session.symptoms.size + session.dtcs.size})",
                        text.session,
                        text.obd,
                        text.analysis,
                        text.activity
                    )

                    Card(Modifier.fillMaxWidth()) {
                        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            Text(text.session, style = MaterialTheme.typography.labelLarge)
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
                            Text(text.symptoms, style = MaterialTheme.typography.titleLarge)
                            OutlinedTextField(
                                value = symptom,
                                onValueChange = { symptom = it },
                                modifier = Modifier.fillMaxWidth(),
                                minLines = 3,
                                maxLines = 5,
                                label = { Text(text.driverSymptom) },
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
                                    ) { Text(text.save) }
                                    Button(
                                        onClick = {
                                            editingSymptomId = null
                                            symptom = ""
                                        },
                                        enabled = !state.loading,
                                        modifier = Modifier.weight(1f)
                                    ) { Text(text.cancel) }
                                }
                            } else {
                                Button(
                                    onClick = {
                                        viewModel.addSymptom(symptom.trim())
                                        symptom = ""
                                    },
                                    enabled = symptom.trim().length >= 3 && symptom.length <= 500 && !state.loading,
                                    modifier = Modifier.fillMaxWidth()
                                ) { Text(text.addSymptom) }
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
                                            ) { Text(text.edit) }
                                            Button(
                                                onClick = {
                                                    viewModel.deleteSymptom(item.id)
                                                    if (editingSymptomId == item.id) {
                                                        editingSymptomId = null
                                                        symptom = ""
                                                    }
                                                },
                                                enabled = !state.loading
                                            ) { Text(text.delete) }
                                        }
                                    }
                                }
                            }

                            Text(text.dtc, style = MaterialTheme.typography.titleLarge)
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
                            ) { Text(text.addDtc) }

                            session.dtcs.forEach { item ->
                                Card(Modifier.fillMaxWidth()) {
                                    Column(Modifier.padding(12.dp)) {
                                        Text(item.code, style = MaterialTheme.typography.titleMedium)
                                        item.description?.let { Text(it) }
                                    }
                                }
                            }

                            Button(
                                onClick = {
                                    selectedTab = 3
                                    if (session.symptoms.isNotEmpty() || session.dtcs.isNotEmpty()) {
                                        viewModel.analyze()
                                    }
                                },
                                enabled = !state.loading &&
                                    (session.symptoms.isNotEmpty() || session.dtcs.isNotEmpty()),
                                modifier = Modifier.fillMaxWidth()
                            ) { Text(text.reviewAnalysis) }
                        }

                        1 -> {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(text.session, style = MaterialTheme.typography.titleLarge)
                                Button(onClick = { editingVehicle = !editingVehicle }, enabled = !state.loading) {
                                    Text(if (editingVehicle) "Cancel" else "Edit")
                                }
                            }

                            if (editingVehicle) {
                                VehicleFields(
                                    text,
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
                                ) { Text(text.saveSession) }
                            } else {
                                Card(Modifier.fillMaxWidth()) {
                                    Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                                        Text(text.vehicle, style = MaterialTheme.typography.labelLarge)
                                        Text("${session.vehicle?.make.orEmpty()} ${session.vehicle?.model.orEmpty()}")
                                        Text("Year: ${session.vehicle?.year ?: "—"}")
                                        Text("Engine: ${session.vehicle?.engine ?: "—"}")
                                        Text("Fuel: ${session.vehicle?.fuel?.joinToString(" + ").orEmpty()}")
                                        Text("ECU: ${session.vehicle?.ecu ?: "—"}")
                                    }
                                }
                            }

                            Button(
                                onClick = { resetForNewSession() },
                                enabled = !state.loading,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text(text.startNewSession) }
                        }

                        2 -> {
                            Text(text.obdConnection, style = MaterialTheme.typography.titleLarge)
                            Text("Bluetooth + Wi-Fi + USB OBD adapters")
                            Text("${text.obdConnection}: ${obdStatus}", fontWeight = FontWeight.Medium)

                            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                Button(onClick = { obdTransport = "bluetooth" }) { Text(text.bluetooth) }
                                Button(onClick = { obdTransport = "wifi" }) { Text(text.wifi) }
                                Button(onClick = { obdTransport = "usb" }) { Text(text.usb) }
                            }

                            when (obdTransport) {
                                "bluetooth" -> {
                                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                        Button(onClick = { refreshBluetoothDevices() }) { Text(text.refresh) }
                                        Button(onClick = {
                                            context.startActivity(Intent(Settings.ACTION_BLUETOOTH_SETTINGS))
                                        }) { Text(text.bluetoothSettings) }
                                    }
                                    if (obdDevices.isEmpty()) {
                                        Text(text.noPairedDevices)
                                    } else {
                                        obdDevices.forEach { device ->
                                            Card(Modifier.fillMaxWidth()) {
                                                Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                                    Text(device.name ?: text.bluetooth, style = MaterialTheme.typography.titleMedium)
                                                    Text(device.address, style = MaterialTheme.typography.bodySmall)
                                                    Button(
                                                        onClick = {
                                                            scope.launch {
                                                                closeAllObd()
                                                                obdTransport = "bluetooth"
                                                                obdStatus = "Connecting Bluetooth..."
                                                                bluetoothClient.connect(device)
                                                                    .onSuccess { obdStatus = it }
                                                                    .onFailure { obdStatus = "Bluetooth error: ${it.message ?: "unknown"}" }
                                                            }
                                                        },
                                                        enabled = !bluetoothClient.isConnected
                                                    ) { Text(text.connect) }
                                                }
                                            }
                                        }
                                    }
                                }

                                "wifi" -> {
                                    OutlinedTextField(
                                        wifiHost,
                                        { wifiHost = it },
                                        Modifier.fillMaxWidth(),
                                        label = { Text(text.host) },
                                        placeholder = { Text("192.168.0.10") }
                                    )
                                    OutlinedTextField(
                                        wifiPort,
                                        { wifiPort = it.filter { ch -> ch.isDigit() }.take(5) },
                                        Modifier.fillMaxWidth(),
                                        label = { Text(text.port) },
                                        placeholder = { Text("35000") }
                                    )
                                    Button(
                                        onClick = {
                                            scope.launch {
                                                closeAllObd()
                                                obdTransport = "wifi"
                                                val port = wifiPort.toIntOrNull() ?: 35000
                                                if (wifiHost.isBlank()) {
                                                    obdStatus = "Enter Wi-Fi host"
                                                } else {
                                                    obdStatus = "Connecting Wi-Fi..."
                                                    wifiClient.connect(wifiHost, port)
                                                        .onSuccess { obdStatus = it }
                                                        .onFailure { obdStatus = "Wi-Fi error: ${it.message ?: "unknown"}" }
                                                }
                                            }
                                        },
                                        enabled = wifiHost.isNotBlank() && !wifiClient.isConnected,
                                        modifier = Modifier.fillMaxWidth()
                                    ) { Text(text.connectWifi) }
                                }

                                "usb" -> {
                                    Button(onClick = { refreshUsbDevices() }) { Text(text.refresh) }
                                    if (usbDevices.isEmpty()) {
                                        Text(text.noUsbDevices)
                                    } else {
                                        usbDevices.forEach { device ->
                                            Card(Modifier.fillMaxWidth()) {
                                                Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                                    Text(
                                                        device.productName ?: device.deviceName,
                                                        style = MaterialTheme.typography.titleMedium
                                                    )
                                                    Text(
                                                        "VID ${device.vendorId} / PID ${device.productId}",
                                                        style = MaterialTheme.typography.bodySmall
                                                    )
                                                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                                        Button(onClick = {
                                                            val manager = context.getSystemService(UsbManager::class.java)
                                                            if (manager != null) {
                                                                val pending = PendingIntent.getBroadcast(
                                                                    context,
                                                                    device.deviceId,
                                                                    Intent("com.aicarscaner.mobile.USB_PERMISSION"),
                                                                    PendingIntent.FLAG_IMMUTABLE
                                                                )
                                                                manager.requestPermission(device, pending)
                                                                obdStatus = "USB permission requested"
                                                            }
                                                        }) { Text(text.requestUsbAccess) }
                                                        Button(
                                                            onClick = {
                                                                scope.launch {
                                                                    val manager = context.getSystemService(UsbManager::class.java)
                                                                    if (manager == null) {
                                                                        obdStatus = "USB manager unavailable"
                                                                    } else {
                                                                        closeAllObd()
                                                                        obdTransport = "usb"
                                                                        obdStatus = "Connecting USB..."
                                                                        usbClient.connect(manager, device)
                                                                            .onSuccess { obdStatus = it }
                                                                            .onFailure { obdStatus = "USB error: ${it.message ?: "unknown"}" }
                                                                    }
                                                                }
                                                            },
                                                            enabled = !usbClient.isConnected
                                                        ) { Text(text.connect) }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }

                            if (bluetoothClient.isConnected || wifiClient.isConnected || usbClient.isConnected) {
                                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                    Button(onClick = {
                                        scope.launch {
                                            when (obdTransport) {
                                                "bluetooth" -> bluetoothClient.command("010C")
                                                "wifi" -> wifiClient.readRpm()
                                                else -> usbClient.readRpm()
                                            }.onSuccess { obdResponse = "RPM: ${it}" }
                                                .onFailure { obdResponse = "RPM read failed: ${it.message ?: "unknown"}" }
                                        }
                                    }) { Text(text.readRpm) }
                                    Button(onClick = {
                                        scope.launch {
                                            when (obdTransport) {
                                                "bluetooth" -> bluetoothClient.command("03")
                                                "wifi" -> wifiClient.readDtcs()
                                                else -> usbClient.readDtcs()
                                            }.onSuccess { obdResponse = "DTC: ${it}" }
                                                .onFailure { obdResponse = "DTC read failed: ${it.message ?: "unknown"}" }
                                        }
                                    }) { Text(text.readDtcs) }
                                    Button(onClick = { closeAllObd() }) { Text(text.disconnect) }
                                }
                            }

                            if (obdResponse.isNotBlank()) {
                                Card(Modifier.fillMaxWidth()) {
                                    Column(Modifier.padding(12.dp)) {
                                        Text(text.adapterResponse, style = MaterialTheme.typography.labelLarge)
                                        Text(obdResponse)
                                    }
                                }
                            }
                        }

                        3 -> {
                            Text(text.analysis, style = MaterialTheme.typography.titleLarge)
                            Button(
                                onClick = { viewModel.analyze() },
                                enabled = !state.loading,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text(text.analyzeSession) }

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
                                Text(text.recommendedTests, style = MaterialTheme.typography.titleMedium)
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
                            Text(text.activity, style = MaterialTheme.typography.titleLarge)
                            if (session.audit_log.isEmpty()) {
                                Text(text.activityEmpty)
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
    text: com.aicarscaner.mobile.settings.AppStrings,
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
    OutlinedTextField(make, onMake, Modifier.fillMaxWidth(), label = { Text(text.make) })
    OutlinedTextField(model, onModel, Modifier.fillMaxWidth(), label = { Text(text.model) })
    OutlinedTextField(year, onYear, Modifier.fillMaxWidth(), label = { Text(text.year) })
    OutlinedTextField(engine, onEngine, Modifier.fillMaxWidth(), label = { Text(text.engine) })

    Text(text.fuel, style = MaterialTheme.typography.titleMedium)
    Row {
        Checkbox(checked = petrol, onCheckedChange = onPetrol)
        Text(text.petrol)
    }
    Row {
        Checkbox(checked = lpg, onCheckedChange = onLpg)
        Text(text.lpg)
    }
}

@Composable
private fun SettingsDialog(
    settings: AppSettings,
    text: com.aicarscaner.mobile.settings.AppStrings,
    onSettingsChanged: (AppSettings) -> Unit,
    onClose: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onClose,
        title = { Text(text.settings) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(text.language, style = MaterialTheme.typography.titleMedium)
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    Button(onClick = { onSettingsChanged(settings.copy(language = AppLanguage.EN)) }) { Text("EN") }
                    Button(onClick = { onSettingsChanged(settings.copy(language = AppLanguage.RU)) }) { Text("RU") }
                    Button(onClick = { onSettingsChanged(settings.copy(language = AppLanguage.HY)) }) { Text("ARM") }
                }
                Text(text.theme, style = MaterialTheme.typography.titleMedium)
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    Button(onClick = { onSettingsChanged(settings.copy(darkTheme = true)) }) { Text(text.dark) }
                    OutlinedButton(onClick = { onSettingsChanged(settings.copy(darkTheme = false)) }) { Text(text.light) }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onClose) { Text(text.close) }
        }
    )
}
