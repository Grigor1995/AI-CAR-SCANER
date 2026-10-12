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
import androidx.compose.material3.IconButton
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
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
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.AlertDialog
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.Icon
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.core.content.ContextCompat
import com.aicarscaner.mobile.data.api.VehicleCatalogEntryDto
import com.aicarscaner.mobile.data.api.VehicleDto
import com.aicarscaner.mobile.data.obd.BluetoothObdClient
import com.aicarscaner.mobile.data.obd.LiveDataReader
import com.aicarscaner.mobile.data.obd.LiveDataSnapshot
import com.aicarscaner.mobile.data.obd.UsbObdClient
import com.aicarscaner.mobile.data.obd.WifiObdClient
import com.aicarscaner.mobile.settings.AppLanguage
import com.aicarscaner.mobile.settings.AppSettings
import com.aicarscaner.mobile.settings.AppSettingsStore
import com.aicarscaner.mobile.settings.strings
import com.aicarscaner.mobile.settings.localizedState
import com.aicarscaner.mobile.settings.localizedEvidenceStatus
import android.app.PendingIntent
import android.hardware.usb.UsbDevice
import android.hardware.usb.UsbManager
import kotlin.math.roundToInt
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch


private val AutomotiveDarkColors = darkColorScheme(
    primary = Color.White,
    onPrimary = Color.Black,
    secondary = Color(0xFFE5E5E5),
    onSecondary = Color.Black,
    tertiary = Color(0xFFD0D0D0),
    background = Color.Black,
    surface = Color(0xFF101010),
    surfaceVariant = Color(0xFF1C1C1C),
    onSurface = Color.White,
    onSurfaceVariant = Color(0xFFB8B8B8),
    error = Color(0xFFFF5A5A)
)

private val AutomotiveLightColors = lightColorScheme(
    primary = Color.Black,
    onPrimary = Color.White,
    secondary = Color(0xFF222222),
    onSecondary = Color.White,
    tertiary = Color(0xFF444444),
    background = Color(0xFFF7F7F7),
    surface = Color.White,
    surfaceVariant = Color(0xFFEAEAEA),
    onSurface = Color.Black,
    onSurfaceVariant = Color(0xFF555555),
    error = Color(0xFFB00020)
)

@Composable
fun DiagnosticScreen(viewModel: DiagnosticViewModel) {
    val state by viewModel.uiState.collectAsState()
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val settingsStore = remember { AppSettingsStore(context) }
    var appSettings by remember { mutableStateOf(settingsStore.load()) }
    var settingsOpen by remember { mutableStateOf(false) }
    var newSessionConfirmOpen by remember { mutableStateOf(false) }
    val text = strings(appSettings.language)
    val extra = text.extra

    val bluetoothClient = remember { BluetoothObdClient() }
    val wifiClient = remember { WifiObdClient() }
    val usbClient = remember { UsbObdClient() }

    var make by remember { mutableStateOf("Mercedes-Benz") }
    var model by remember { mutableStateOf("E-Class") }
    var chassis by remember { mutableStateOf("W211") }
    var year by remember { mutableStateOf("2006") }
    var engine by remember { mutableStateOf("M272 E35 3.5") }
    var ecu by remember { mutableStateOf("ME9.7") }
    var petrol by remember { mutableStateOf(true) }
    var lpg by remember { mutableStateOf(true) }
    var symptom by remember { mutableStateOf("") }
    var editingSymptomId by remember { mutableStateOf<String?>(null) }
    var dtc by remember { mutableStateOf("") }
    var editingDtcId by remember { mutableStateOf<String?>(null) }
    var selectedTab by remember { mutableIntStateOf(0) }
    var editingVehicle by remember { mutableStateOf(false) }
    var obdDevices by remember { mutableStateOf<List<BluetoothDevice>>(emptyList()) }
    var usbDevices by remember { mutableStateOf<List<UsbDevice>>(emptyList()) }
    var wifiHost by remember { mutableStateOf("") }
    var wifiPort by remember { mutableStateOf("35000") }
    var obdStatus by remember { mutableStateOf(text.notConnected) }
    var obdResponse by remember { mutableStateOf("") }
    var obdTransport by remember { mutableStateOf("bluetooth") }
    var liveDataRunning by remember { mutableStateOf(false) }
    var liveData by remember { mutableStateOf<LiveDataSnapshot?>(null) }
    var liveDataError by remember { mutableStateOf<String?>(null) }
    var testResultDialogOpen by remember { mutableStateOf(false) }
    var selectedTestId by remember { mutableStateOf<String?>(null) }
    var selectedTestTitle by remember { mutableStateOf("") }
    var testOutcome by remember { mutableStateOf("INCOMPLETE") }
    var testNotes by remember { mutableStateOf("") }

    val bluetoothPermission = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        arrayOf(
            Manifest.permission.BLUETOOTH_CONNECT,
            Manifest.permission.BLUETOOTH_SCAN
        )
    } else {
        emptyArray()
    }

    fun refreshUsbDevices() {
        val manager = context.getSystemService(UsbManager::class.java)
        usbDevices = manager?.deviceList?.values?.toList() ?: emptyList()
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

    fun closeAllObd() {
        liveDataRunning = false
        liveData = null
        liveDataError = null
        bluetoothClient.close()
        wifiClient.close()
        usbClient.close()
        obdStatus = text.notConnected
        obdResponse = ""
    }

    fun resetForNewSession() {
        closeAllObd()
        viewModel.clearSession()
        selectedTab = 0
        editingVehicle = false
        editingSymptomId = null
        symptom = ""
        dtc = ""
        editingDtcId = null
        make = "Mercedes-Benz"
        model = "E-Class"
        chassis = "W211"
        year = "2006"
        engine = "M272 E35 3.5"
        ecu = "ME9.7"
        petrol = true
        lpg = true
    }

    LaunchedEffect(Unit) {
        viewModel.loadVehicleCatalog()
        refreshBluetoothDevices()
        refreshUsbDevices()
    }

    fun applyRemoteMake(value: String): Boolean {
        val remoteModels = modelOptionsFor(state.vehicleCatalog, value)
        if (remoteModels.isEmpty()) return false
        make = value
        model = remoteModels.first()
        chassis = chassisOptionsFor(state.vehicleCatalog, make, model).firstOrNull().orEmpty()
        year = yearOptionsFor(state.vehicleCatalog, make, model, chassis).firstOrNull()?.toString().orEmpty()
        engine = engineOptionsFor(state.vehicleCatalog, make, model, chassis, year.toIntOrNull()).firstOrNull().orEmpty()
        ecu = ecuOptionsFor(state.vehicleCatalog, make, model, chassis, engine, year.toIntOrNull()).firstOrNull().orEmpty()
        return true
    }

    fun applyRemoteModel(value: String): Boolean {
        val remoteChassis = chassisOptionsFor(state.vehicleCatalog, make, value)
        if (remoteChassis.isEmpty()) return false
        model = value
        chassis = remoteChassis.first()
        year = yearOptionsFor(state.vehicleCatalog, make, model, chassis).firstOrNull()?.toString().orEmpty()
        engine = engineOptionsFor(state.vehicleCatalog, make, model, chassis, year.toIntOrNull()).firstOrNull().orEmpty()
        ecu = ecuOptionsFor(state.vehicleCatalog, make, model, chassis, engine, year.toIntOrNull()).firstOrNull().orEmpty()
        return true
    }

    fun applyRemoteChassis(value: String): Boolean {
        val years = yearOptionsFor(state.vehicleCatalog, make, model, value)
        if (years.isEmpty()) return false
        chassis = value
        year = years.first().toString()
        engine = engineOptionsFor(state.vehicleCatalog, make, model, chassis, year.toIntOrNull()).firstOrNull().orEmpty()
        ecu = ecuOptionsFor(state.vehicleCatalog, make, model, chassis, engine, year.toIntOrNull()).firstOrNull().orEmpty()
        return true
    }

    fun applyRemoteEngine(value: String): Boolean {
        val ecus = ecuOptionsFor(state.vehicleCatalog, make, model, chassis, value, year.toIntOrNull())
        if (ecus.isEmpty()) return false
        engine = value
        ecu = ecus.first()
        return true
    }

    val obdConnected =
        bluetoothClient.isConnected || wifiClient.isConnected || usbClient.isConnected

    LaunchedEffect(liveDataRunning, obdTransport, obdConnected) {
        if (!liveDataRunning || !obdConnected) {
            return@LaunchedEffect
        }

        while (isActive) {
            LiveDataReader.read { command ->
                when (obdTransport) {
                    "bluetooth" -> bluetoothClient.command(command)
                    "wifi" -> wifiClient.command(command)
                    else -> usbClient.command(command)
                }
            }.onSuccess {
                liveData = it
                liveDataError = if (
                    it.rpm == null &&
                    it.speedKph == null &&
                    it.coolantC == null &&
                    it.engineLoadPct == null
                ) text.noLiveData else null
            }.onFailure {
                liveDataError = it.message ?: extra.liveDataReadFailed
            }
            delay(1200)
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            bluetoothClient.close()
            wifiClient.close()
            usbClient.close()
        }
    }

    MaterialTheme(
        colorScheme = if (appSettings.darkTheme) AutomotiveDarkColors else AutomotiveLightColors
    ) {
        if (settingsOpen) {
            SettingsDialog(
                settings = appSettings,
                text = text,
                onSettingsChanged = {
                    appSettings = it
                    settingsStore.save(it)
                },
                onLanguageChanged = { language ->
                    val active = state.session
                    if (active != null && (active.symptoms.isNotEmpty() || active.dtcs.isNotEmpty())) {
                        viewModel.analyze(language.code)
                    }
                },
                onClose = { settingsOpen = false }
            )
        }

        if (newSessionConfirmOpen) {
            AlertDialog(
                onDismissRequest = { newSessionConfirmOpen = false },
                title = { Text(text.newSessionConfirmTitle) },
                text = { Text(text.newSessionConfirmMessage) },
                confirmButton = {
                    Button(
                        onClick = {
                            newSessionConfirmOpen = false
                            resetForNewSession()
                        },
                        enabled = !state.loading
                    ) { Text(text.startNewSession) }
                },
                dismissButton = {
                    TextButton(onClick = { newSessionConfirmOpen = false }) {
                        Text(text.cancel)
                    }
                }
            )
        }

        if (testResultDialogOpen) {
            AlertDialog(
                onDismissRequest = { testResultDialogOpen = false },
                title = { Text(selectedTestTitle) },
                text = {
                    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        Text(extra.nextDiagnostic, style = MaterialTheme.typography.labelLarge)
                        Text(extra.nextDiagnosticResult, style = MaterialTheme.typography.labelLarge)
                        Row(
                            Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            listOf(
                                "PASS" to extra.pass,
                                "FAIL" to extra.fail,
                                "INCOMPLETE" to extra.incomplete
                            ).forEach { (value, label) ->
                                if (testOutcome == value) {
                                    Button(
                                        onClick = { testOutcome = value },
                                        modifier = Modifier.weight(1f)
                                    ) { Text(label, maxLines = 1) }
                                } else {
                                    OutlinedButton(
                                        onClick = { testOutcome = value },
                                        modifier = Modifier.weight(1f)
                                    ) { Text(label, maxLines = 1) }
                                }
                            }
                        }
                        OutlinedTextField(
                            value = testNotes,
                            onValueChange = { testNotes = it },
                            modifier = Modifier.fillMaxWidth(),
                            minLines = 3,
                            maxLines = 6,
                            label = { Text(extra.diagnosticNotes) },
                            placeholder = { Text(extra.notesPlaceholder) }
                        )
                    }
                },
                confirmButton = {
                    Button(
                        onClick = {
                            val id = selectedTestId
                            if (id != null) {
                                testResultDialogOpen = false
                                viewModel.recordTestResult(
                                    id,
                                    testOutcome,
                                    testNotes.takeIf { it.isNotBlank() },
                                    appSettings.language.code
                                )
                            }
                        },
                        enabled = selectedTestId != null && testOutcome.isNotBlank() && !state.loading
                    ) { Text(extra.recordResult) }
                },
                dismissButton = {
                    TextButton(onClick = { testResultDialogOpen = false }) {
                        Text(text.cancel)
                    }
                }
            )
        }

        Surface(modifier = Modifier.fillMaxSize()) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = androidx.compose.ui.Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column(Modifier.weight(1f)) {
                            Text(
                                text.appName,
                                style = MaterialTheme.typography.headlineMedium,
                                fontWeight = FontWeight.Bold
                            )
                            state.session?.let {
                                Text(
                                    "${text.extra.session} ${it.session_id.take(8)}…",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }

                        Row(horizontalArrangement = Arrangement.spacedBy(2.dp)) {
                            IconButton(
                                onClick = { settingsOpen = true },
                                enabled = true,
                                modifier = Modifier
                            ) {
                                Text("⚙", style = MaterialTheme.typography.titleLarge)
                            }
                            if (state.session != null) {
                                IconButton(
                                    onClick = { newSessionConfirmOpen = true },
                                    enabled = true,
                                    modifier = Modifier
                                ) {
                                    Icon(Icons.Outlined.Add, contentDescription = text.newSession)
                                }
                            }
                        }
                    }

                    androidx.compose.material3.HorizontalDivider(
                        color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.12f)
                    )
                }

                if (state.session == null) {
                    Text(
                        text.newSession,
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.SemiBold
                    )
                    VehicleFields(
                        text = text,
                        catalog = state.vehicleCatalog,
                        make = make,
                        onMake = { value ->
                            if (!applyRemoteMake(value)) {
                                make = value
                                val nextModel = modelOptionsFor(value).firstOrNull()
                                model = nextModel?.name.orEmpty()
                                chassis = nextModel?.chassis.orEmpty()
                                year = nextModel?.years?.firstOrNull()?.toString().orEmpty()
                                engine = nextModel?.engines?.firstOrNull()?.name.orEmpty()
                                ecu = nextModel?.engines?.firstOrNull()?.ecus?.firstOrNull().orEmpty()
                            }
                        },
                        model = model,
                        onModel = { value ->
                            if (!applyRemoteModel(value)) {
                                model = value
                                val nextModel = modelOptionsFor(make).firstOrNull { it.name == value }
                                chassis = nextModel?.chassis.orEmpty()
                                year = nextModel?.years?.firstOrNull()?.toString().orEmpty()
                                engine = nextModel?.engines?.firstOrNull()?.name.orEmpty()
                                ecu = nextModel?.engines?.firstOrNull()?.ecus?.firstOrNull().orEmpty()
                            }
                        },
                        chassis = chassis,
                        onChassis = { value ->
                            if (!applyRemoteChassis(value)) {
                                chassis = value
                                val nextModel = modelOptionsFor(make).firstOrNull { it.name == model && it.chassis == value }
                                year = nextModel?.years?.firstOrNull()?.toString().orEmpty()
                                engine = nextModel?.engines?.firstOrNull()?.name.orEmpty()
                                ecu = nextModel?.engines?.firstOrNull()?.ecus?.firstOrNull().orEmpty()
                            }
                        },
                        year = year,
                        onYear = { value ->
                            year = value
                            ecu = ecuOptionsFor(state.vehicleCatalog, make, model, chassis, engine, value.toIntOrNull()).firstOrNull()
                                ?: ecuOptionsFor(make, model, chassis, engine).firstOrNull().orEmpty()
                        },
                        engine = engine,
                        onEngine = {
                            if (!applyRemoteEngine(it)) {
                                engine = it
                                ecu = ecuOptionsFor(make, model, chassis, it).firstOrNull().orEmpty()
                            }
                        },
                        ecu = ecu,
                        onEcu = { ecu = it },
                        petrol,
                        onPetrol = { petrol = it },
                        lpg,
                        onLpg = { lpg = it }
                    )
                    Button(
                        onClick = {
                            viewModel.createSession(
                                VehicleDto(make, model, chassis, year.toIntOrNull(), engine, buildList {
                                    if (petrol) add("petrol")
                                    if (lpg) add("LPG")
                                }, ecu)
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
                            chassis = vehicle.chassis.orEmpty()
                            year = vehicle.year?.toString().orEmpty()
                            engine = vehicle.engine.orEmpty()
                            ecu = vehicle.ecu ?: ecuOptionsFor(vehicle.make, vehicle.model, vehicle.chassis.orEmpty(), vehicle.engine.orEmpty()).firstOrNull().orEmpty()
                            petrol = vehicle.fuel.any { it.equals("petrol", true) }
                            lpg = vehicle.fuel.any { it.equals("lpg", true) }
                        }
                    }

                    val tabs = listOf(
                        "${text.diagnose} (${session.symptoms.size + session.dtcs.size})",
                        text.session,
                        text.obd,
                        text.liveData,
                        text.analysis,
                        text.activity
                    )

                    Card(
                                        Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(16.dp),
                                        colors = CardDefaults.cardColors(
                                            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)
                                        )
                                    ) {
                        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            Text(text.session, style = MaterialTheme.typography.labelLarge)
                            Text(session.vehicle?.let { "${it.make} ${it.model}${if (it.chassis.isNullOrBlank()) "" else " / ${it.chassis}"}" } ?: extra.vehicleNotIdentified)
                            Text("${extra.state}: ${localizedState(appSettings.language, session.state)}", style = MaterialTheme.typography.bodySmall)
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
                                placeholder = { Text(extra.symptomExample) },
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
                                Card(
                                        Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(16.dp),
                                        colors = CardDefaults.cardColors(
                                            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)
                                        )
                                    ) {
                                    Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                                        Text("${extra.symptomItem} ${index + 1}", style = MaterialTheme.typography.labelLarge)
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
                                                enabled = !state.loading,
                                                colors = ButtonDefaults.buttonColors(
                                                    containerColor = MaterialTheme.colorScheme.error,
                                                    contentColor = MaterialTheme.colorScheme.onError
                                                )
                                            ) { Text(text.delete) }
                                        }
                                    }
                                }
                            }

                            Text(text.dtc, style = MaterialTheme.typography.titleLarge)
                            OutlinedTextField(
                                value = dtc,
                                onValueChange = { dtc = it.uppercase() },
                                modifier = Modifier.fillMaxWidth(),
                                label = { Text(extra.diagnosticTroubleCode) },
                                placeholder = { Text("P0302") }
                            )

                            if (editingDtcId != null) {
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    Button(
                                        onClick = {
                                            viewModel.updateDtc(editingDtcId!!, dtc.trim())
                                            editingDtcId = null
                                            dtc = ""
                                        },
                                        enabled = dtc.trim().isNotEmpty() && !state.loading,
                                        modifier = Modifier.weight(1f)
                                    ) { Text(text.save) }

                                    OutlinedButton(
                                        onClick = {
                                            editingDtcId = null
                                            dtc = ""
                                        },
                                        enabled = !state.loading,
                                        modifier = Modifier.weight(1f)
                                    ) { Text(text.cancel) }
                                }
                            } else {
                                Button(
                                    onClick = {
                                        viewModel.addDtc(dtc.trim())
                                        dtc = ""
                                    },
                                    enabled = dtc.trim().isNotEmpty() && !state.loading,
                                    modifier = Modifier.fillMaxWidth()
                                ) { Text(text.addDtc) }
                            }

                            session.dtcs.forEach { item ->
                                Card(
                                    Modifier.fillMaxWidth(),
                                    shape = RoundedCornerShape(16.dp),
                                    colors = CardDefaults.cardColors(
                                        containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)
                                    )
                                ) {
                                    Column(
                                        Modifier.padding(12.dp),
                                        verticalArrangement = Arrangement.spacedBy(6.dp)
                                    ) {
                                        Row(
                                            Modifier.fillMaxWidth(),
                                            horizontalArrangement = Arrangement.SpaceBetween
                                        ) {
                                            Column(Modifier.weight(1f)) {
                                                Text(item.code, style = MaterialTheme.typography.titleMedium)
                                                item.description?.let { Text(it) }
                                            }
                                            if (item.id != null) {
                                                Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                                    OutlinedButton(
                                                        onClick = {
                                                            dtc = item.code
                                                            editingDtcId = item.id
                                                        },
                                                        enabled = !state.loading
                                                    ) { Text(text.edit) }

                                                    Button(
                                                        onClick = {
                                                            viewModel.deleteDtc(item.id)
                                                            if (editingDtcId == item.id) {
                                                                editingDtcId = null
                                                                dtc = ""
                                                            }
                                                        },
                                                        enabled = !state.loading,
                                                        colors = ButtonDefaults.buttonColors(
                                                            containerColor = MaterialTheme.colorScheme.error,
                                                            contentColor = MaterialTheme.colorScheme.onError
                                                        )
                                                    ) { Text(text.delete) }
                                                }
                                            }
                                        }
                                    }
                                }
                            }

                            Button(
                                onClick = {
                                    selectedTab = 4
                                    if (session.symptoms.isNotEmpty() || session.dtcs.isNotEmpty()) {
                                        viewModel.analyze(appSettings.language.code)
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
                                    Text(if (editingVehicle) text.cancel else text.edit)
                                }
                            }

                            if (editingVehicle) {
                                VehicleFields(
                                    text = text,
                                    catalog = state.vehicleCatalog,
                                    make = make,
                                    onMake = { value ->
                                        if (!applyRemoteMake(value)) {
                                            make = value
                                            val nextModel = modelOptionsFor(value).firstOrNull()
                                            model = nextModel?.name.orEmpty()
                                            chassis = nextModel?.chassis.orEmpty()
                                            year = nextModel?.years?.firstOrNull()?.toString().orEmpty()
                                            engine = nextModel?.engines?.firstOrNull()?.name.orEmpty()
                                            ecu = nextModel?.engines?.firstOrNull()?.ecus?.firstOrNull().orEmpty()
                                        }
                                    },
                                    model = model,
                                    onModel = { value ->
                                        if (!applyRemoteModel(value)) {
                                            model = value
                                            val nextModel = modelOptionsFor(make).firstOrNull { it.name == value }
                                            chassis = nextModel?.chassis.orEmpty()
                                            year = nextModel?.years?.firstOrNull()?.toString().orEmpty()
                                            engine = nextModel?.engines?.firstOrNull()?.name.orEmpty()
                                            ecu = nextModel?.engines?.firstOrNull()?.ecus?.firstOrNull().orEmpty()
                                        }
                                    },
                                    chassis = chassis,
                                    onChassis = { value ->
                                        if (!applyRemoteChassis(value)) {
                                            chassis = value
                                            year = yearOptionsFor(make, model, value).firstOrNull()?.toString().orEmpty()
                                            engine = engineOptionsFor(make, model, value).firstOrNull()?.name.orEmpty()
                                            ecu = ecuOptionsFor(make, model, value, engine).firstOrNull().orEmpty()
                                        }
                                    },
                                    year = year,
                                    onYear = { value ->
                                        year = value
                                        ecu = ecuOptionsFor(state.vehicleCatalog, make, model, chassis, engine, value.toIntOrNull()).firstOrNull()
                                            ?: ecuOptionsFor(make, model, chassis, engine).firstOrNull().orEmpty()
                                    },
                                    engine = engine,
                                    onEngine = {
                                        if (!applyRemoteEngine(it)) {
                                            engine = it
                                            ecu = ecuOptionsFor(make, model, chassis, it).firstOrNull().orEmpty()
                                        }
                                    },
                                    ecu = ecu,
                                    onEcu = { ecu = it },
                                    petrol = petrol,
                                    onPetrol = { petrol = it },
                                    lpg = lpg,
                                    onLpg = { lpg = it }
                                )
                                Button(
                                    onClick = {
                                        viewModel.updateVehicle(
                                            VehicleDto(make, model, chassis, year.toIntOrNull(), engine, buildList {
                                                if (petrol) add("petrol")
                                                if (lpg) add("LPG")
                                            }, ecu)
                                        )
                                        editingVehicle = false
                                    },
                                    enabled = !state.loading,
                                    modifier = Modifier.fillMaxWidth()
                                ) { Text(text.saveSession) }
                            } else {
                                Card(
                                        Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(16.dp),
                                        colors = CardDefaults.cardColors(
                                            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)
                                        )
                                    ) {
                                    Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                                        Text(text.vehicle, style = MaterialTheme.typography.labelLarge)
                                        Text("${session.vehicle?.make.orEmpty()} ${session.vehicle?.model.orEmpty()}")
                                        Text("${text.chassis}: ${session.vehicle?.chassis ?: "—"}")
                                        Text("${text.year}: ${session.vehicle?.year ?: "—"}")
                                        Text("${text.engine}: ${session.vehicle?.engine ?: "—"}")
                                        Text("${text.fuel}: ${session.vehicle?.fuel?.joinToString(" + ") { fuel -> when (fuel.lowercase()) { "petrol" -> text.petrol; "lpg" -> text.lpg; else -> fuel } }.orEmpty()}")
                                        Text("${extra.ecu}: ${session.vehicle?.ecu ?: "—"}")
                                    }
                                }
                            }

                            Button(
                                onClick = { newSessionConfirmOpen = true },
                                enabled = !state.loading,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text(text.startNewSession) }
                        }

                        2 -> {
                            Text(text.obdConnection, style = MaterialTheme.typography.titleLarge)
                            Text(extra.obdAdapters)
                            Text("${text.obdConnection}: ${obdStatus}", fontWeight = FontWeight.Medium)

                            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                TransportButton(obdTransport == "bluetooth", { obdTransport = "bluetooth" }, text.bluetooth)
                                TransportButton(obdTransport == "wifi", { obdTransport = "wifi" }, text.wifi)
                                TransportButton(obdTransport == "usb", { obdTransport = "usb" }, text.usb)
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
                                            Card(
                                        Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(16.dp),
                                        colors = CardDefaults.cardColors(
                                            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)
                                        )
                                    ) {
                                                Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                                                    Text(device.name ?: text.bluetooth, style = MaterialTheme.typography.titleMedium)
                                                    Text(device.address, style = MaterialTheme.typography.bodySmall)
                                                    Button(
                                                        onClick = {
                                                            scope.launch {
                                                                closeAllObd()
                                                                obdTransport = "bluetooth"
                                                                obdStatus = extra.connectingBluetooth
                                                                bluetoothClient.connect(device)
                                                                    .onSuccess { obdStatus = it }
                                                                    .onFailure { obdStatus = "${extra.bluetoothError}: ${it.message ?: extra.incompleteError}" }
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
                                                    obdStatus = extra.enterWifiHost
                                                } else {
                                                    obdStatus = extra.connectingWifi
                                                    wifiClient.connect(wifiHost, port)
                                                        .onSuccess { obdStatus = it }
                                                        .onFailure { obdStatus = "${extra.wifiError}: ${it.message ?: extra.incompleteError}" }
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
                                            Card(
                                        Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(16.dp),
                                        colors = CardDefaults.cardColors(
                                            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)
                                        )
                                    ) {
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
                                                                obdStatus = extra.usbPermissionRequested
                                                            }
                                                        }) { Text(text.requestUsbAccess) }
                                                        Button(
                                                            onClick = {
                                                                scope.launch {
                                                                    val manager = context.getSystemService(UsbManager::class.java)
                                                                    if (manager == null) {
                                                                        obdStatus = extra.usbManagerUnavailable
                                                                    } else {
                                                                        closeAllObd()
                                                                        obdTransport = "usb"
                                                                        obdStatus = extra.connectingUsb
                                                                        usbClient.connect(manager, device)
                                                                            .onSuccess { obdStatus = it }
                                                                            .onFailure { obdStatus = "${extra.usbError}: ${it.message ?: extra.incompleteError}" }
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
                                            }.onSuccess { obdResponse = "${extra.rpmValue}: ${it}" }
                                                .onFailure { obdResponse = "${extra.rpmReadFailed}: ${it.message ?: extra.incompleteError}" }
                                        }
                                    }) { Text(text.readRpm) }
                                    Button(onClick = {
                                        scope.launch {
                                            when (obdTransport) {
                                                "bluetooth" -> bluetoothClient.command("03")
                                                "wifi" -> wifiClient.readDtcs()
                                                else -> usbClient.readDtcs()
                                            }.onSuccess { obdResponse = "${extra.dtcValue}: ${it}" }
                                                .onFailure { obdResponse = "${extra.dtcReadFailed}: ${it.message ?: extra.incompleteError}" }
                                        }
                                    }) { Text(text.readDtcs) }
                                    Button(onClick = { closeAllObd() }) { Text(text.disconnect) }
                                }
                            }

                            if (obdResponse.isNotBlank()) {
                                Card(
                                        Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(16.dp),
                                        colors = CardDefaults.cardColors(
                                            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)
                                        )
                                    ) {
                                    Column(Modifier.padding(12.dp)) {
                                        Text(text.adapterResponse, style = MaterialTheme.typography.labelLarge)
                                        Text(obdResponse)
                                    }
                                }
                            }
                        }

                        3 -> {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Column {
                                    Text(text.liveData, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                                    Text(
                                        if (obdConnected) text.connected else text.liveDataDisconnected,
                                        style = MaterialTheme.typography.bodySmall,
                                        color = if (obdConnected) MaterialTheme.colorScheme.secondary else MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                                Button(
                                    onClick = {
                                        if (liveDataRunning) {
                                            liveDataRunning = false
                                        } else {
                                            liveDataError = null
                                            liveDataRunning = true
                                        }
                                    },
                                    enabled = obdConnected,
                                    colors = ButtonDefaults.buttonColors(
                                        containerColor = if (liveDataRunning) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.secondary,
                                        contentColor = if (liveDataRunning) MaterialTheme.colorScheme.onError else MaterialTheme.colorScheme.onSecondary
                                    ),
                                    shape = RoundedCornerShape(12.dp)
                                ) {
                                    Text(if (liveDataRunning) text.stopLiveData else text.startLiveData)
                                }
                            }

                            if (!obdConnected) {
                                Card(
                                    Modifier.fillMaxWidth(),
                                    shape = RoundedCornerShape(16.dp),
                                    colors = CardDefaults.cardColors(
                                        containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)
                                    )
                                ) {
                                    Text(
                                        text.liveDataDisconnected,
                                        modifier = Modifier.padding(18.dp),
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                            } else {
                                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                    LiveDataTile(text.rpm, liveData?.rpm?.let { "%.0f".format(it) } ?: "—", "rpm", Modifier.weight(1f), true)
                                    LiveDataTile(text.speed, liveData?.speedKph?.let { "%.0f".format(it) } ?: "—", "km/h", Modifier.weight(1f), true)
                                }
                                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                    LiveDataTile(text.coolantTemp, liveData?.coolantC?.let { "%.0f".format(it) } ?: "—", "°C", Modifier.weight(1f))
                                    LiveDataTile(text.engineLoad, liveData?.engineLoadPct?.let { "%.1f".format(it) } ?: "—", "%", Modifier.weight(1f))
                                }
                                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                    LiveDataTile(text.intakeAirTemp, liveData?.intakeAirC?.let { "%.0f".format(it) } ?: "—", "°C", Modifier.weight(1f))
                                    LiveDataTile(text.map, liveData?.mapKpa?.let { "%.0f".format(it) } ?: "—", "kPa", Modifier.weight(1f))
                                }
                                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                    LiveDataTile(text.maf, liveData?.mafGps?.let { "%.1f".format(it) } ?: "—", "g/s", Modifier.weight(1f))
                                    LiveDataTile(text.throttle, liveData?.throttlePct?.let { "%.1f".format(it) } ?: "—", "%", Modifier.weight(1f))
                                }
                                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                    LiveDataTile(text.stft, liveData?.shortFuelTrimPct?.let { "%+.1f".format(it) } ?: "—", "%", Modifier.weight(1f))
                                    LiveDataTile(text.ltft, liveData?.longFuelTrimPct?.let { "%+.1f".format(it) } ?: "—", "%", Modifier.weight(1f))
                                }
                            }

                            liveDataError?.let {
                                Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                            }
                        }

                        4 -> {
                            Text(text.analysis, style = MaterialTheme.typography.titleLarge)

                            if (session.hypotheses.isEmpty() && session.recommendations.isEmpty()) {
                                Card(
                                    Modifier.fillMaxWidth(),
                                    shape = RoundedCornerShape(16.dp),
                                    colors = CardDefaults.cardColors(
                                        containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)
                                    )
                                ) {
                                    Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                        Text(
                                            text.analysisEmpty,
                                            style = MaterialTheme.typography.bodyLarge,
                                            fontWeight = FontWeight.Medium
                                        )
                                        Text(
                                            "${text.symptoms}: ${session.symptoms.size}  •  ${text.dtc}: ${session.dtcs.size}  •  ${text.evidence}: ${session.evidence.size}",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }
                                }
                            } else {
                                val evidenceById = session.evidence.associateBy { it.id }
                                val latestQuestions = session.audit_log.flatMap { it.questions.orEmpty() }.distinct()

                                Card(
                                    Modifier.fillMaxWidth(),
                                    shape = RoundedCornerShape(16.dp),
                                    colors = CardDefaults.cardColors(
                                        containerColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.08f)
                                    )
                                ) {
                                    Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                        Text(text.evidence, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                                        Text(
                                            "${text.symptoms}: ${session.symptoms.size}  •  ${text.dtc}: ${session.dtcs.size}  •  ${text.evidence}: ${session.evidence.size}  •  ${text.analysis}: ${session.hypotheses.size}",
                                            style = MaterialTheme.typography.bodySmall
                                        )
                                        Text(
                                            session.evidence.groupingBy { it.status.lowercase() }.eachCount().entries
                                                .joinToString(" • ") { "${localizedEvidenceStatus(appSettings.language, it.key, extra)}: ${it.value}" },
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }
                                }

                                session.hypotheses.forEachIndexed { index, hypothesis ->
                                    val supporting = hypothesis.supporting_evidence_ids.mapNotNull { evidenceById[it] }
                                    val contradicting = hypothesis.contradicting_evidence_ids.mapNotNull { evidenceById[it] }
                                    val confidence = hypothesis.status.substringAfter(":", "").toDoubleOrNull()

                                    Card(
                                        Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(16.dp),
                                        colors = CardDefaults.cardColors(
                                            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)
                                        )
                                    ) {
                                        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                                            Text(
                                                "${index + 1}. ${hypothesis.category}",
                                                style = MaterialTheme.typography.titleMedium,
                                                fontWeight = FontWeight.SemiBold
                                            )
                                            Row(
                                                Modifier.fillMaxWidth(),
                                                horizontalArrangement = Arrangement.SpaceBetween
                                            ) {
                                                Text(hypothesis.status, style = MaterialTheme.typography.labelLarge)
                                                confidence?.let {
                                                    Text(
                                                        "${text.confidence}: ${(it * 100).roundToInt()}%",
                                                        style = MaterialTheme.typography.labelLarge
                                                    )
                                                }
                                            }
                                            Text(hypothesis.statement)

                                            if (supporting.isNotEmpty()) {
                                                Text(text.supportingEvidence, style = MaterialTheme.typography.labelLarge)
                                                supporting.forEach { evidence ->
                                                    Text(
                                                        "• ${evidence.fact} [${when (evidence.status.lowercase()) { "reported" -> extra.reported; "measured" -> extra.measured; "calculated" -> extra.calculated; "inferred" -> extra.inferred; "confirmed" -> extra.confirmed; "rejected" -> extra.rejectedStatus; else -> evidence.status }}]",
                                                        style = MaterialTheme.typography.bodySmall
                                                    )
                                                }
                                            }

                                            if (contradicting.isNotEmpty()) {
                                                Text(text.contradictingEvidence, style = MaterialTheme.typography.labelLarge)
                                                contradicting.forEach { evidence ->
                                                    Text(
                                                        "• ${evidence.fact} [${when (evidence.status.lowercase()) { "reported" -> extra.reported; "measured" -> extra.measured; "calculated" -> extra.calculated; "inferred" -> extra.inferred; "confirmed" -> extra.confirmed; "rejected" -> extra.rejectedStatus; else -> evidence.status }}]",
                                                        style = MaterialTheme.typography.bodySmall,
                                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                                    )
                                                }
                                            }
                                        }
                                    }
                                }

                                if (session.test_results.isNotEmpty()) {
                                    Card(
                                        Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(16.dp),
                                        colors = CardDefaults.cardColors(
                                            containerColor = MaterialTheme.colorScheme.secondary.copy(alpha = 0.08f)
                                        )
                                    ) {
                                        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                            Text(extra.nextDiagnosticResult, style = MaterialTheme.typography.titleMedium)
                                            session.test_results.takeLast(5).reversed().forEach { result ->
                                                val resultLabel = when (result.result.uppercase()) {
                                                    "PASS" -> extra.pass
                                                    "FAIL" -> extra.fail
                                                    "INCOMPLETE" -> extra.incomplete
                                                    else -> result.result
                                                }
                                                Text(
                                                    result.testName ?: (extra.nextDiagnostic + " #" + result.test_id.take(8)),
                                                    fontWeight = FontWeight.SemiBold
                                                )
                                                Text(
                                                    extra.nextDiagnosticResult + ": " + resultLabel,
                                                    style = MaterialTheme.typography.bodySmall
                                                )
                                                result.notes?.takeIf { it.isNotBlank() }?.let {
                                                    Text(it, style = MaterialTheme.typography.bodySmall)
                                                }
                                            }
                                        }
                                    }
                                }

                                if (latestQuestions.isNotEmpty()) {
                                    Card(
                                        Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(16.dp),
                                        colors = CardDefaults.cardColors(
                                            containerColor = MaterialTheme.colorScheme.tertiary.copy(alpha = 0.10f)
                                        )
                                    ) {
                                        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                            Text(text.nextQuestions, style = MaterialTheme.typography.titleMedium)
                                            latestQuestions.forEach { question -> Text("• $question") }
                                        }
                                    }
                                }

                                if (session.recommendations.isNotEmpty()) {
                                    val nextTest = session.recommendations.first()

                                    Card(
                                        Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(16.dp),
                                        colors = CardDefaults.cardColors(
                                            containerColor = MaterialTheme.colorScheme.secondary.copy(alpha = 0.10f)
                                        )
                                    ) {
                                        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                            Text(extra.nextDiagnostic, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                                            Text(nextTest.title, fontWeight = FontWeight.Medium)
                                            Text(nextTest.purpose, style = MaterialTheme.typography.bodySmall)
                                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                                Button(
                                                    onClick = {
                                                        selectedTestId = nextTest.id
                                                        selectedTestTitle = nextTest.title
                                                        testOutcome = "INCOMPLETE"
                                                        testNotes = ""
                                                        testResultDialogOpen = true
                                                    },
                                                    enabled = !state.loading,
                                                    modifier = Modifier.weight(1f)
                                                ) { Text(extra.recordResult, maxLines = 1) }

                                                OutlinedButton(
                                                    onClick = {
                                                        selectedTab = 3
                                                        liveDataError = null
                                                        if (obdConnected) liveDataRunning = true
                                                    },
                                                    enabled = !state.loading,
                                                    modifier = Modifier.weight(1f)
                                                ) { Text(extra.openLiveData, maxLines = 1) }
                                            }
                                        }
                                    }

                                    Text(text.recommendedTests, style = MaterialTheme.typography.titleMedium)
                                    session.recommendations.forEachIndexed { index, recommendation ->
                                        Card(
                                            Modifier.fillMaxWidth(),
                                            shape = RoundedCornerShape(16.dp),
                                            colors = CardDefaults.cardColors(
                                                containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)
                                            )
                                        ) {
                                            Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                                                Text(
                                                    "${index + 1}. ${recommendation.title}",
                                                    style = MaterialTheme.typography.titleMedium,
                                                    fontWeight = FontWeight.SemiBold
                                                )
                                                Text(recommendation.purpose)
                                                Row(
                                                    Modifier.fillMaxWidth(),
                                                    horizontalArrangement = Arrangement.SpaceBetween
                                                ) {
                                                    Text("${text.priority}: ${(recommendation.priority * 100).roundToInt()}%")
                                                    Text("${text.informationGain}: ${(recommendation.informationGain * 100).roundToInt()}%")
                                                }
                                                Row(
                                                    Modifier.fillMaxWidth(),
                                                    horizontalArrangement = Arrangement.SpaceBetween
                                                ) {
                                                    Text("${text.risk}: ${when (recommendation.riskLevel.uppercase()) { "LOW" -> extra.low; "MEDIUM" -> extra.medium; "HIGH" -> extra.high; else -> recommendation.riskLevel }}")
                                                    Text("${text.estimatedCost}: %.1f".format(recommendation.estimatedCost))
                                                }
                                                recommendation.expected_observation?.takeIf { it.isNotBlank() }?.let {
                                                    Text(it, style = MaterialTheme.typography.bodySmall)
                                                }

                                                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                                    OutlinedButton(
                                                        onClick = {
                                                            selectedTestId = recommendation.id
                                                            selectedTestTitle = recommendation.title
                                                            testOutcome = "INCOMPLETE"
                                                            testNotes = ""
                                                            testResultDialogOpen = true
                                                        },
                                                        enabled = !state.loading,
                                                        modifier = Modifier.weight(1f)
                                                    ) { Text(extra.recordResult, maxLines = 1) }

                                                    OutlinedButton(
                                                        onClick = {
                                                            selectedTab = 3
                                                            liveDataError = null
                                                            if (obdConnected) liveDataRunning = true
                                                        },
                                                        enabled = !state.loading,
                                                        modifier = Modifier.weight(1f)
                                                    ) { Text(extra.openLiveData, maxLines = 1) }
                                                }
                                            }
                                        }
                                    }
                                }
                            }

                            Button(
                                onClick = { viewModel.analyze(appSettings.language.code) },
                                enabled = !state.loading &&
                                    (session.symptoms.isNotEmpty() || session.dtcs.isNotEmpty()),
                                modifier = Modifier.fillMaxWidth(),
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = MaterialTheme.colorScheme.primary,
                                    contentColor = MaterialTheme.colorScheme.onPrimary
                                ),
                                shape = RoundedCornerShape(12.dp)
                            ) { Text(text.analyzeSession) }
                        }

                        5 -> {
                            Text(text.activity, style = MaterialTheme.typography.titleLarge)
                            if (session.audit_log.isEmpty()) {
                                Text(text.activityEmpty)
                            } else {
                                session.audit_log.forEach { event ->
                                    Card(
                                        Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(16.dp),
                                        colors = CardDefaults.cardColors(
                                            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)
                                        )
                                    ) {
                                        Column(Modifier.padding(12.dp)) {
                                            Text(event.event, style = MaterialTheme.typography.labelLarge)
                                            event.hypotheses?.let { Text("${extra.hypotheses}: ${it}", style = MaterialTheme.typography.bodySmall) }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            if (state.loading) CircularProgressIndicator()
            state.error?.let { Text("${extra.error}: ${it}", color = MaterialTheme.colorScheme.error) }
        }
    }
}

@Composable
private fun TransportButton(
    selected: Boolean,
    onClick: () -> Unit,
    label: String
) {
    if (selected) {
        Button(
            onClick = onClick,
            colors = ButtonDefaults.buttonColors(
                containerColor = MaterialTheme.colorScheme.primary,
                contentColor = MaterialTheme.colorScheme.onPrimary
            ),
            shape = RoundedCornerShape(10.dp)
        ) { Text(label) }
    } else {
        OutlinedButton(onClick = onClick, shape = RoundedCornerShape(10.dp)) {
            Text(label)
        }
    }
}

@Composable
private fun LiveDataTile(
    label: String,
    value: String,
    unit: String,
    modifier: Modifier = Modifier,
    highlight: Boolean = false
) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (highlight) {
                MaterialTheme.colorScheme.primary.copy(alpha = 0.12f)
            } else {
                MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)
            }
        )
    ) {
        Column(
            Modifier.padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            Text(
                label,
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Row(verticalAlignment = androidx.compose.ui.Alignment.Bottom) {
                Text(value, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                Text(
                    " $unit",
                    style = MaterialTheme.typography.labelMedium,
                    modifier = Modifier.padding(bottom = 3.dp),
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
private fun VehicleFields(
    text: com.aicarscaner.mobile.settings.AppStrings,
    catalog: List<VehicleCatalogEntryDto>,
    make: String,
    onMake: (String) -> Unit,
    model: String,
    onModel: (String) -> Unit,
    chassis: String,
    onChassis: (String) -> Unit,
    year: String,
    onYear: (String) -> Unit,
    engine: String,
    onEngine: (String) -> Unit,
    ecu: String,
    onEcu: (String) -> Unit,
    petrol: Boolean,
    onPetrol: (Boolean) -> Unit,
    lpg: Boolean,
    onLpg: (Boolean) -> Unit
) {
    val makes = modelOptionsFor(catalog, make).let { 
        catalog.map { it.make }.distinct().sorted().ifEmpty { vehicleCatalog.map { it.name } }
    }
    val models = modelOptionsFor(catalog, make).ifEmpty { modelOptionsFor(make).map { it.name }.distinct() }
    val chassisOptions = chassisOptionsFor(catalog, make, model).ifEmpty { chassisOptionsFor(make, model).map { it.chassis } }
    val years = yearOptionsFor(catalog, make, model, chassis).map(Int::toString).ifEmpty { yearOptionsFor(make, model, chassis).map(Int::toString) }
    val engines = engineOptionsFor(catalog, make, model, chassis, year.toIntOrNull()).ifEmpty { engineOptionsFor(make, model, chassis).map { it.name } }
    val ecus = ecuOptionsFor(catalog, make, model, chassis, engine, year.toIntOrNull()).ifEmpty { ecuOptionsFor(make, model, chassis, engine) }

    VehicleSelectionField(text.make, make, makes, onMake)
    VehicleSelectionField(text.model, model, models, onModel)
    VehicleSelectionField(text.chassis, chassis, chassisOptions, onChassis)
    VehicleSelectionField(text.year, year, years, onYear)
    VehicleSelectionField(text.engine, engine, engines, onEngine)
    VehicleSelectionField(text.extra.ecu, ecu, ecus, onEcu)

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

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun VehicleSelectionField(
    label: String,
    value: String,
    options: List<String>,
    onSelected: (String) -> Unit
) {
    var expanded by remember(value, options) { mutableStateOf(false) }

    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = {
            if (options.isNotEmpty()) expanded = !expanded
        },
        modifier = Modifier.fillMaxWidth()
    ) {
        OutlinedTextField(
            value = value,
            onValueChange = {},
            readOnly = true,
            singleLine = true,
            modifier = Modifier
                .fillMaxWidth()
                .menuAnchor(),
            label = { Text(label) },
            trailingIcon = {
                androidx.compose.material3.ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded)
            }
        )
        ExposedDropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false }
        ) {
            options.forEach { option ->
                DropdownMenuItem(
                    text = { Text(option) },
                    onClick = {
                        onSelected(option)
                        expanded = false
                    }
                )
            }
        }
    }
}

@Composable
private fun SettingsDialog(
    settings: AppSettings,
    text: com.aicarscaner.mobile.settings.AppStrings,
    onSettingsChanged: (AppSettings) -> Unit,
    onLanguageChanged: (AppLanguage) -> Unit,
    onClose: () -> Unit
) {
    MaterialTheme(
        colorScheme = if (settings.darkTheme) AutomotiveDarkColors else AutomotiveLightColors
    ) {
        AlertDialog(
            onDismissRequest = onClose,
            title = { Text(text.settings) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text(text.language, style = MaterialTheme.typography.titleMedium)
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        if (settings.language == AppLanguage.EN) {
                            Button(onClick = { onSettingsChanged(settings.copy(language = AppLanguage.EN)); onLanguageChanged(AppLanguage.EN) }) { Text("EN") }
                        } else {
                            OutlinedButton(onClick = { onSettingsChanged(settings.copy(language = AppLanguage.EN)); onLanguageChanged(AppLanguage.EN) }) { Text("EN") }
                        }
                        if (settings.language == AppLanguage.RU) {
                            Button(onClick = { onSettingsChanged(settings.copy(language = AppLanguage.RU)); onLanguageChanged(AppLanguage.RU) }) { Text("RU") }
                        } else {
                            OutlinedButton(onClick = { onSettingsChanged(settings.copy(language = AppLanguage.RU)); onLanguageChanged(AppLanguage.RU) }) { Text("RU") }
                        }
                        if (settings.language == AppLanguage.HY) {
                            Button(onClick = { onSettingsChanged(settings.copy(language = AppLanguage.HY)); onLanguageChanged(AppLanguage.HY) }) { Text("ARM") }
                        } else {
                            OutlinedButton(onClick = { onSettingsChanged(settings.copy(language = AppLanguage.HY)); onLanguageChanged(AppLanguage.HY) }) { Text("ARM") }
                        }
                    }
                    Text(text.theme, style = MaterialTheme.typography.titleMedium)
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        if (settings.darkTheme) {
                            Button(onClick = { onSettingsChanged(settings.copy(darkTheme = true)) }) { Text(text.dark) }
                        } else {
                            OutlinedButton(onClick = { onSettingsChanged(settings.copy(darkTheme = true)) }) { Text(text.dark) }
                        }
                        if (!settings.darkTheme) {
                            Button(onClick = { onSettingsChanged(settings.copy(darkTheme = false)) }) { Text(text.light) }
                        } else {
                            OutlinedButton(onClick = { onSettingsChanged(settings.copy(darkTheme = false)) }) { Text(text.light) }
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = onClose) { Text(text.close) }
            }
        )
    }
}
