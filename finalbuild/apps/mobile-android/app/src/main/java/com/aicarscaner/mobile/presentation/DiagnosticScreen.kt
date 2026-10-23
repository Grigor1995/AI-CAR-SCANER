package com.aicarscaner.mobile.presentation

import android.graphics.BitmapFactory
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import android.Manifest
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothManager
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.provider.Settings
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.Surface
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.MenuAnchorType
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.TextButton
import androidx.compose.runtime.CompositionLocalProvider
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
import androidx.compose.ui.graphics.Brush
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
import com.aicarscaner.mobile.settings.localizedConnectionStatus
import com.aicarscaner.mobile.settings.localizedState
import com.aicarscaner.mobile.settings.localizedEvidenceStatus
import android.app.PendingIntent
import android.hardware.usb.UsbDevice
import android.hardware.usb.UsbManager
import kotlin.math.roundToInt
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.coroutines.launch


// Color tokens follow the shared blue / cyan / violet automotive UI reference.
// Semantic status colors remain independently green (PASS), red (FAIL), amber (INCOMPLETE).
internal val AutomotiveDarkColors = darkColorScheme(
    primary = Color(0xFF188AFF),
    onPrimary = Color.White,
    secondary = Color(0xFF9C74FF),
    onSecondary = Color.White,
    tertiary = Color(0xFF28D5FF),
    background = Color(0xFF061121),
    surface = Color(0xFF0C1C35),
    surfaceVariant = Color(0xFF102640),
    onBackground = Color(0xFFEAF4FF),
    primaryContainer = Color(0xFF103E63),
    onPrimaryContainer = Color(0xFFEAF4FF),
    secondaryContainer = Color(0xFF30254C),
    onSecondaryContainer = Color(0xFFEAF4FF),
    onSurface = Color(0xFFEAF4FF),
    onSurfaceVariant = Color(0xFFAAC8E5),
    error = Color(0xFFFF617A)
)

internal val AutomotiveLightColors = lightColorScheme(
    primary = Color(0xFF096BCD),
    onPrimary = Color.White,
    secondary = Color(0xFF7050BA),
    onSecondary = Color.White,
    tertiary = Color(0xFF096E98),
    background = Color(0xFFF0F6FC),
    surface = Color.White,
    surfaceVariant = Color(0xFFE2EFFC),
    onBackground = Color(0xFF10243F),
    primaryContainer = Color(0xFFD8EBFF),
    onPrimaryContainer = Color(0xFF10243F),
    secondaryContainer = Color(0xFFE8DEFF),
    onSecondaryContainer = Color(0xFF10243F),
    onSurface = Color(0xFF10243F),
    onSurfaceVariant = Color(0xFF4F6D8F),
    error = Color(0xFFB71E43)
)


@Composable
fun DiagnosticScreen(viewModel: DiagnosticViewModel) {
    val state by viewModel.uiState.collectAsState()
    val context = LocalContext.current
    val catalog = state.vehicleCatalog
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
    var selectedTab by remember { mutableIntStateOf(6) }
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
    var channelHistory by remember { mutableStateOf<List<LiveDataSnapshot>>(emptyList()) }
    LaunchedEffect(liveData, state.session?.session_id) {
        val sample = liveData
        if (sample != null) channelHistory = (channelHistory + sample).takeLast(60)
    }
    LaunchedEffect(state.session?.session_id) { channelHistory = emptyList(); liveData = null; liveDataRunning = false }
    fun demo(en: String, ru: String, hy: String): String = when (appSettings.language) {
        AppLanguage.RU -> ru
        AppLanguage.HY -> hy
        else -> en
    }
    var liveDataError by remember { mutableStateOf<String?>(null) }
    var testResultDialogOpen by remember { mutableStateOf(false) }
    var selectedTestId by remember { mutableStateOf<String?>(null) }
    var selectedTestTitle by remember { mutableStateOf("") }
    var testOutcome by remember { mutableStateOf("INCOMPLETE") }
    var testNotes by remember { mutableStateOf("") }
    var pendingTestRevision by remember { mutableStateOf<Int?>(null) }
    val pageScrollState = rememberScrollState()
    LaunchedEffect(selectedTab, state.testResultRevision) {
        pageScrollState.scrollTo(0)
    }
    LaunchedEffect(state.testResultRevision, state.testResultCompletion, state.loading, state.error) {
        val submittedAt = pendingTestRevision
        if (submittedAt != null && !state.loading) {
            if (state.testResultRevision > submittedAt) {
                pendingTestRevision = null
                testResultDialogOpen = false
                selectedTab = 4
            } else if (state.error != null) {
                pendingTestRevision = null
            }
        }
    }

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
        selectedTab = 6
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
        // Keep first render free of hardware discovery and runtime permission prompts.
        // Bluetooth and USB devices are refreshed from the OBD screen when the user opens it.
        viewModel.loadVehicleCatalog()
    }

    fun applyRemoteMake(value: String): Boolean {
        val remoteModels = modelOptionsFor(catalog, value)
        if (remoteModels.isEmpty()) return false
        make = value
        model = remoteModels.first()
        chassis = chassisOptionsFor(catalog, make, model).firstOrNull().orEmpty()
        year = yearOptionsFor(catalog, make, model, chassis).firstOrNull()?.toString().orEmpty()
        engine = engineOptionsFor(catalog, make, model, chassis, year.toIntOrNull()).firstOrNull().orEmpty()
        ecu = ecuOptionsFor(catalog, make, model, chassis, engine, year.toIntOrNull()).firstOrNull().orEmpty()
        return true
    }

    fun applyRemoteModel(value: String): Boolean {
        val remoteChassis = chassisOptionsFor(catalog, make, value)
        if (remoteChassis.isEmpty()) return false
        model = value
        chassis = remoteChassis.first()
        year = yearOptionsFor(catalog, make, model, chassis).firstOrNull()?.toString().orEmpty()
        engine = engineOptionsFor(catalog, make, model, chassis, year.toIntOrNull()).firstOrNull().orEmpty()
        ecu = ecuOptionsFor(catalog, make, model, chassis, engine, year.toIntOrNull()).firstOrNull().orEmpty()
        return true
    }

    fun applyRemoteChassis(value: String): Boolean {
        val years = yearOptionsFor(catalog, make, model, value)
        if (years.isEmpty()) return false
        chassis = value
        year = years.first().toString()
        engine = engineOptionsFor(catalog, make, model, chassis, year.toIntOrNull()).firstOrNull().orEmpty()
        ecu = ecuOptionsFor(catalog, make, model, chassis, engine, year.toIntOrNull()).firstOrNull().orEmpty()
        return true
    }

    fun applyRemoteEngine(value: String): Boolean {
        val ecus = ecuOptionsFor(catalog, make, model, chassis, value, year.toIntOrNull())
        if (value !in engineOptionsFor(catalog, make, model, chassis, year.toIntOrNull())) return false
        engine = value
        ecu = ecus.firstOrNull().orEmpty()
        return true
    }

    val obdConnected =
        bluetoothClient.isConnected || wifiClient.isConnected || usbClient.isConnected

    var discoveryPending by remember { mutableStateOf(false) }
    var discoveryResult by remember { mutableStateOf<com.aicarscaner.mobile.data.api.DiscoveryResultDto?>(null) }
    var discoveryError by remember { mutableStateOf(false) }
    val adapterPanel: @Composable () -> Unit = {
                            DemoAdapterHeader(obdConnected,localizedConnectionStatus(appSettings.language,obdStatus))
                            Text(text.obdConnection, style = MaterialTheme.typography.titleLarge)
                            Text(extra.obdAdapters)
                            Text("${text.obdConnection}: ${localizedConnectionStatus(appSettings.language,obdStatus)}", fontWeight = FontWeight.Medium)

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
                                        border = BorderStroke(
                                            1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.38f)
                                        ),
                                        colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,
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
                                                                    .onFailure { obdStatus = "${extra.bluetoothError}: ${it.message ?: extra.unknownError}" }
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
                                                        .onFailure { obdStatus = "${extra.wifiError}: ${it.message ?: extra.unknownError}" }
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
                                        border = BorderStroke(
                                            1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.38f)
                                        ),
                                        colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,
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
                                                                            .onFailure { obdStatus = "${extra.usbError}: ${it.message ?: extra.unknownError}" }
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
                                                .onFailure { obdResponse = "${extra.rpmReadFailed}: ${it.message ?: extra.unknownError}" }
                                        }
                                    }) { Text(text.readRpm) }
                                    Button(onClick = {
                                        scope.launch {
                                            when (obdTransport) {
                                                "bluetooth" -> bluetoothClient.command("03")
                                                "wifi" -> wifiClient.readDtcs()
                                                else -> usbClient.readDtcs()
                                            }.onSuccess { obdResponse = "${extra.dtcValue}: ${it}" }
                                                .onFailure { obdResponse = "${extra.dtcReadFailed}: ${it.message ?: extra.unknownError}" }
                                        }
                                    }) { Text(text.readDtcs) }
                                    Button(onClick = { closeAllObd() }) { Text(text.disconnect) }
                                }
                            }

                            if (obdResponse.isNotBlank()) {
                                Card(
                                        Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(16.dp),
                                        border = BorderStroke(
                                            1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.38f)
                                        ),
                                        colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,
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
    var identifyAfterConnect by remember { mutableStateOf(false) }
    fun discoverConnectedVehicle() {
            val discoveryTransport=obdTransport
            discoveryPending=true;discoveryResult=null;discoveryError=false
            scope.launch {
                suspend fun command(step:String):String = when(discoveryTransport) {
                    "bluetooth" -> bluetoothClient.command(step,35000)
                    "wifi" -> wifiClient.command(step,35000)
                    else -> usbClient.command(step,35000)
                }.getOrThrow()
                try {
                    discoveryResult=com.aicarscaner.mobile.data.obd.DiscoveryReader.read { command(it) }
                } catch(cancelled:kotlinx.coroutines.CancellationException) { throw cancelled }
                catch(error:Exception) { discoveryError=true }
                finally { discoveryPending=false }
            }
    }
    LaunchedEffect(obdConnected,identifyAfterConnect) {
        if(obdConnected && identifyAfterConnect) {
            identifyAfterConnect=false
            selectedTab=14
            discoverConnectedVehicle()
        }
    }
    val diagnosticPanel: @Composable () -> Unit = {
        Text(dashboardLabel("Diagnostics"),style=MaterialTheme.typography.titleLarge)
        Text(dashboardLabel("VIN lookup uses NHTSA online. Only responding generic OBD ECUs are shown."))
        OutlinedButton(onClick={selectedTab=2;refreshUsbDevices()},enabled=!discoveryPending,modifier=Modifier.fillMaxWidth()) {
            Text(dashboardLabel("VCI / Devices"))
        }
        Button(enabled=!discoveryPending && !liveDataRunning,onClick={
            if(obdConnected) discoverConnectedVehicle()
            else { identifyAfterConnect=true;selectedTab=2;refreshUsbDevices() }
        },modifier=Modifier.fillMaxWidth()) { Text(dashboardLabel("Connect OBD and identify vehicle")) }
        if(liveDataRunning) Text(dashboardLabel("Stop live data before discovery"))
        if(discoveryPending) { CircularProgressIndicator(); Text(dashboardLabel("Reading VIN and identifying vehicle…")) }
        if(discoveryError) Text(dashboardLabel("OBD connection failed. Check adapter and ignition."))
        discoveryResult?.let { result ->
            val status=when(result.identification_status) {
                "identified" -> "Vehicle identified"; "incomplete" -> "Vehicle identification incomplete"
                "lookup_unavailable" -> "VIN lookup unavailable"; "simulated" -> "Simulator / synthetic data"
                else -> "VIN unavailable"
            }
            DemoPanel(dashboardLabel(status)) {
                Text("VIN: "+(result.vin ?: "—"))
                result.vehicle?.let { vehicle -> Text(listOfNotNull(vehicle.make,vehicle.model,vehicle.model_year,vehicle.engine_model).joinToString(" · ")) }
            }
            result.modules.forEach { module -> DemoPanel(dashboardLabel("OBD ECU")) { Text(module.address ?: "—") } }
            if(result.modules.isEmpty()) Text(dashboardLabel("No responding OBD ECUs detected"))
        }
    }

    LaunchedEffect(liveDataRunning, obdTransport, obdConnected, discoveryPending) {
        if (!liveDataRunning || !obdConnected || discoveryPending) {
            return@LaunchedEffect
        }

        while (isActive) {
            LiveDataReader.read(sessionId = state.session?.session_id) { command ->
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
        CompositionLocalProvider(LocalDashboardLanguage provides appSettings.language, LocalDashboardUsUnits provides appSettings.usUnits, LocalDashboardAnalog provides appSettings.analogDisplay) {
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
                    if (active != null) {
                        viewModel.openSession(active.session_id, language.code)
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
                onDismissRequest = { if (pendingTestRevision == null) testResultDialogOpen = false },
                title = { Text(selectedTestTitle) },
                text = {
                    Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        if (pendingTestRevision != null) {
                            CircularProgressIndicator()
                            Text(dashboardLabel("Updating diagnosis…"))
                        }
                        state.error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                        Text(extra.nextDiagnostic, style = MaterialTheme.typography.labelLarge)
                        Text(extra.nextDiagnosticResult, style = MaterialTheme.typography.labelLarge)
                        Column(
                            Modifier.fillMaxWidth(),
                            verticalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            listOf(
                                "PASS" to extra.pass,
                                "FAIL" to extra.fail,
                                "INCOMPLETE" to extra.incomplete
                            ).forEach { (value, label) ->
                                if (testOutcome == value) {
                                    Button(
                                        onClick = { testOutcome = value },
                                        modifier = Modifier.fillMaxWidth(),
                                        colors = ButtonDefaults.buttonColors(
                                            containerColor = when (value) {
                                                "PASS" -> Color(0xFF0B956E)
                                                "FAIL" -> Color(0xFFC83253)
                                                else -> Color(0xFF54729C)
                                            }
                                        )
                                    ) { Text(label) }
                                } else {
                                    OutlinedButton(
                                        onClick = { testOutcome = value },
                                        modifier = Modifier.fillMaxWidth()
                                    ) { Text(label) }
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
                                pendingTestRevision = state.testResultRevision
                                viewModel.recordTestResult(
                                    id,
                                    testOutcome,
                                    testNotes.takeIf { it.isNotBlank() },
                                    appSettings.language.code
                                )
                            }
                        },
                        enabled = selectedTestId != null && testOutcome.isNotBlank() && !state.loading && pendingTestRevision == null
                    ) { Text(extra.recordResult) }
                },
                dismissButton = {
                    TextButton(onClick = { testResultDialogOpen = false }, enabled = pendingTestRevision == null) {
                        Text(text.cancel)
                    }
                }
            )
        }

        Surface(
            modifier = Modifier.fillMaxSize().background(
                Brush.verticalGradient(
                    colors = if (appSettings.darkTheme) listOf(
                        Color(0xFF051329), Color(0xFF061121), Color(0xFF07172D)
                    ) else listOf(Color(0xFFF0F6FC), Color(0xFFEAF4FF))
                )
            ),
            color = Color.Transparent,
            contentColor = MaterialTheme.colorScheme.onBackground
        ) {
            Scaffold(containerColor = Color.Transparent, contentColor = MaterialTheme.colorScheme.onBackground, topBar = {
                Column(Modifier.fillMaxWidth().background(MaterialTheme.colorScheme.surface).statusBarsPadding().padding(horizontal=16.dp,vertical=8.dp),verticalArrangement=Arrangement.spacedBy(6.dp)) {
                    DashboardToolbar(
                        title=if(state.session==null || selectedTab==6) "AI CAR SCANNER" else dashboardLabel(when(selectedTab){1->"Vehicles";2->"VCI / Devices";0->"Symptoms";14->"Diagnostic";7->"DTC";4->"AI Analysis";8->"Tests";3->"Live Data";9->"Reports";10->"Teach AI";12->"Custom dashboard";13->"Testing progress";5->"Activity";else->"More"}),
                        hasSession=state.session!=null && selectedTab!=14,
                        showSettings=selectedTab !in listOf(0,14),
                        showBack=selectedTab !in listOf(6,9),
                        loading=state.loading,
                        onHome={selectedTab=6},
                        onSettings={settingsOpen=true},
                        onNewSession={newSessionConfirmOpen=true},
                        onSymptoms={selectedTab=0},
                        onAnalyze={selectedTab=4;viewModel.analyze(appSettings.language.code)}
                    )
                }
            }, bottomBar = {
                if (state.session != null) DashboardBottomBar(selectedTab) { destination ->
                    selectedTab = destination
                    if (destination == 2) refreshUsbDevices()
                    if (destination == 9) viewModel.loadHistory()
                }
            }) { insets ->
            Column(
                modifier = Modifier
                    .fillMaxSize().padding(insets)
                    .verticalScroll(pageScrollState)
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                if(selectedTab==14) {
                    diagnosticPanel()
                } else if(state.session==null && selectedTab==2) {
                    adapterPanel()
                } else if (state.session == null) {
                    OutlinedButton(onClick={selectedTab=14},modifier=Modifier.fillMaxWidth()) { Text(dashboardLabel("Connect OBD and identify vehicle")) }
                    OutlinedButton(onClick = { selectedTab = 9; viewModel.loadHistory() }, modifier = Modifier.fillMaxWidth()) {
                        Text(demo("Reports / History", "Отчёты / История", "Հաշվետվություններ / Պատմություն"))
                    }
                    if (selectedTab == 9) state.history.forEach { previous ->
                        DemoPanel(previous.vehicle?.let { "${it.make} ${it.model}" } ?: dashboardLabel("Diagnostic report")) {
                            Text("${localizedState(appSettings.language,previous.state)}")
                            Button(onClick = { viewModel.openSession(previous.session_id, appSettings.language.code); selectedTab = 6 }) {
                                Text(demo("Open session", "Открыть сеанс", "Բացել սեսիան"))
                            }
                        }
                    }
                    Text(
                        text.newSession,
                        style = MaterialTheme.typography.headlineSmall,
                        fontWeight = FontWeight.SemiBold
                    )
                    if (!state.catalogOnline) {
                        Text(
                            when (appSettings.language) {
                                AppLanguage.RU -> "Офлайн-каталог: список может отличаться от серверного каталога."
                                AppLanguage.HY -> "Օֆլայն կատալոգ․ ցանկը կարող է տարբերվել սերվերի կատալոգից։"
                                else -> "Offline catalog: options may differ from the server catalog."
                            },
                            color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                    VehicleFields(
                        text = text,
                        catalog = catalog,
                        make = make,
                        onMake = { value ->
                            applyRemoteMake(value)
                        },
                        model = model,
                        onModel = { value ->
                            applyRemoteModel(value)
                        },
                        chassis = chassis,
                        onChassis = { value ->
                            applyRemoteChassis(value)
                        },
                        year = year,
                        onYear = { value ->
                            year = value
                            engine = engineOptionsFor(catalog, make, model, chassis, value.toIntOrNull()).firstOrNull().orEmpty()
                            ecu = ecuOptionsFor(catalog, make, model, chassis, engine, value.toIntOrNull()).firstOrNull().orEmpty()
                        },
                        engine = engine,
                        onEngine = {
                            applyRemoteEngine(it)
                        },
                        ecu = ecu,
                        onEcu = { ecu = it },
                        petrol,
                        onPetrol = { petrol = it },
                        lpg,
                        onLpg = { lpg = it },
                        language = appSettings.language
                    )
                    Button(
                        onClick = {
                            viewModel.createSession(
                                VehicleDto(make, model, chassis, year.toIntOrNull(), engine, formFuel(catalog, make, model, chassis, engine, petrol, lpg), ecu)
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
                            ecu = vehicle.ecu ?: ecuOptionsFor(state.vehicleCatalog, vehicle.make, vehicle.model, vehicle.chassis.orEmpty(), vehicle.engine.orEmpty(), vehicle.year).firstOrNull().orEmpty()
                            petrol = vehicle.fuel.any { it.equals("petrol", true) }
                            lpg = vehicle.fuel.any { it.equals("lpg", true) }
                        }
                    }

                    val tabs = listOf(
                        "${text.symptoms} (${session.symptoms.size})",
                        text.session,
                        text.obd,
                        text.liveData,
                        text.analysis,
                        text.activity,
                        demo("Home", "Обзор", "Գլխավոր"),
                        "DTC",
                        demo("Guided Tests", "Тесты", "Փորձարկումներ"),
                        demo("Reports", "Отчёты", "Հաշվետվություններ"),
                        demo("Teach AI", "Обучить ИИ", "Սովորեցնել AI-ին")
                    )

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
                                        border = BorderStroke(
                                            1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.38f)
                                        ),
                                        colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,
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
                                        border = BorderStroke(
                                            1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.38f)
                                        ),
                                    colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,
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

                        14 -> diagnosticPanel()

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
                                if (!state.catalogOnline) {
                                    Text(
                                        when (appSettings.language) {
                                            AppLanguage.RU -> "Офлайн-каталог: список может отличаться от серверного каталога."
                                            AppLanguage.HY -> "Օֆլայն կատալոգ․ ցանկը կարող է տարբերվել սերվերի կատալոգից։"
                                            else -> "Offline catalog: options may differ from the server catalog."
                                        },
                                        color = MaterialTheme.colorScheme.error,
                                        style = MaterialTheme.typography.bodySmall
                                    )
                                }
                                VehicleFields(
                                    text = text,
                                    catalog = catalog,
                                    make = make,
                                    onMake = { value ->
                                        applyRemoteMake(value)
                                    },
                                    model = model,
                                    onModel = { value ->
                                        applyRemoteModel(value)
                                    },
                                    chassis = chassis,
                                    onChassis = { value ->
                                        applyRemoteChassis(value)
                                    },
                                    year = year,
                                    onYear = { value ->
                                        year = value
                                        engine = engineOptionsFor(catalog, make, model, chassis, value.toIntOrNull()).firstOrNull().orEmpty()
                                        ecu = ecuOptionsFor(catalog, make, model, chassis, engine, value.toIntOrNull()).firstOrNull().orEmpty()
                                    },
                                    engine = engine,
                                    onEngine = {
                                        applyRemoteEngine(it)
                                    },
                                    ecu = ecu,
                                    onEcu = { ecu = it },
                                    petrol = petrol,
                                    onPetrol = { petrol = it },
                                    lpg = lpg,
                                    onLpg = { lpg = it },
                        language = appSettings.language
                                )
                                Button(
                                    onClick = {
                                        viewModel.updateVehicle(
                                            VehicleDto(make, model, chassis, year.toIntOrNull(), engine, formFuel(catalog, make, model, chassis, engine, petrol, lpg), ecu)
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
                                        border = BorderStroke(
                                            1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.38f)
                                        ),
                                        colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,
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

                        2 -> adapterPanel()

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
                                        border = BorderStroke(
                                            1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.38f)
                                        ),
                                    colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,
                                        containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)
                                    )
                                ) {
                                    Text(
                                        text.liveDataDisconnected,
                                        modifier = Modifier.padding(18.dp),
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                            }
                            DemoPanel(demo("Backend acquisition records", "Записи сервера", "Սերվերի չափումներ")) {
                                Text(
                                    demo("Stored server samples; not local OBD live streaming.",
                                         "Сохранённые данные сервера, не локальный OBD-поток.",
                                         "Սերվերում պահպանված չափումներ, ոչ տեղային OBD հոսք։"),
                                    style = MaterialTheme.typography.bodySmall
                                )
                                OutlinedButton(
                                    onClick = { viewModel.refreshBackendLiveRecords() },
                                    enabled = state.session != null && !state.backendLiveLoading
                                ) {
                                    Text(demo("Refresh server samples", "Обновить данные сервера", "Թարմացնել սերվերի տվյալները"))
                                }
                                if (state.backendLiveLoading) CircularProgressIndicator()
                                state.backendLiveError?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                                if (!state.backendLiveLoading && state.backendLiveRecords.isEmpty()) {
                                    Text(demo("No server samples", "Нет записей сервера", "Սերվերի չափումներ չկան"))
                                }
                                DemoBackendLiveCharts(state.backendLiveRecords)
                            }
                            OutlinedButton(onClick={selectedTab=12},modifier=Modifier.fillMaxWidth()) {Text(dashboardLabel("Custom dashboard")+" ›")}

                            if (channelHistory.isNotEmpty() || state.backendLiveRecords.isEmpty()) DemoLiveCharts(channelHistory)
                            liveDataError?.let {
                                Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                            }
                        }

                        4 -> {
                            AnalysisWorkspace(
                                session=session, loading=state.loading,
                                resultRevision=state.testResultRevision,
                                onAnalyze={viewModel.analyze(appSettings.language.code)},
                                onRecord={id,title ->
                                    selectedTestId=id
                                    selectedTestTitle=title
                                    testOutcome="INCOMPLETE"
                                    testNotes=""
                                    testResultDialogOpen=true
                                })
                            var advanced by remember { mutableStateOf(false) }
                            TextButton(onClick={advanced=!advanced}) { Text(dashboardLabel(if(advanced) "Hide details" else "Advanced analysis")) }
                            if(advanced) {
                            Text(text.analysis, style = MaterialTheme.typography.titleLarge)

                            if (session.hypotheses.isEmpty() && session.recommendations.isEmpty()) {
                                Card(
                                    Modifier.fillMaxWidth(),
                                    shape = RoundedCornerShape(16.dp),
                                        border = BorderStroke(
                                            1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.38f)
                                        ),
                                    colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,
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
                                        border = BorderStroke(
                                            1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.38f)
                                        ),
                                    colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,
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
                                        border = BorderStroke(
                                            1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.38f)
                                        ),
                                        colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,
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
                                        border = BorderStroke(
                                            1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.38f)
                                        ),
                                        colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,
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
                                        border = BorderStroke(
                                            1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.38f)
                                        ),
                                        colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,
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
                                        border = BorderStroke(
                                            1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.38f)
                                        ),
                                        colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,
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
                                        border = BorderStroke(
                                            1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.38f)
                                        ),
                                            colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,
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
                        }

                        6 -> { DemoHome(session, tabs) { selectedTab = it }; DemoPanel(dashboardLabel("Live Data / Custom dashboard")) { if (channelHistory.isEmpty() && state.backendLiveRecords.isNotEmpty()) DemoBackendLiveCharts(state.backendLiveRecords) else DemoLiveCharts(channelHistory, dashboard=true) } }
                        11 -> DashboardSections(navigate={selectedTab=it;if(it==2) refreshUsbDevices()},settings={settingsOpen=true})
                        12 -> if (channelHistory.isEmpty() && state.backendLiveRecords.isNotEmpty()) DemoBackendLiveCharts(state.backendLiveRecords) else DemoLiveCharts(channelHistory,dashboard=true)
                        13 -> DemoProgress(session) {selectedTab=8}
                        7 -> DemoDtcList(session, "DTC")
                        8 -> DemoGuidedTests(session, tabs[8]) { id, title ->
                            selectedTestId = id
                            selectedTestTitle = title
                            testOutcome = "INCOMPLETE"
                            testNotes = ""
                            testResultDialogOpen = true
                        }
                        9 -> {
                            LaunchedEffect(Unit) { viewModel.loadHistory() }
                            OutlinedButton(onClick = { viewModel.loadHistory() }) { Text(demo("Refresh history", "Обновить историю", "Թարմացնել պատմությունը")) }
                            state.history.forEach { previous ->
                                DemoPanel(previous.vehicle?.let { "${it.make} ${it.model}" } ?: dashboardLabel("Diagnostic report")) {
                                    Text("DTC: ${previous.dtcs.size} • ${localizedState(appSettings.language,previous.state)}")
                                    Button(onClick = { viewModel.openSession(previous.session_id, appSettings.language.code); selectedTab = 6 }) { Text(demo("Open session", "Открыть сеанс", "Բացել սեսիան")) }
                                }
                            }
                            DemoReports(session, tabs[9], demo("Share session report", "Поделиться отчётом", "Կիսվել հաշվետվությամբ"))
                        }
                        10 -> DemoTeach(tabs[10], demo("Draft saved on this device; no model training", "Черновик на устройстве; без обучения модели", "Սևագիրը պահվում է սարքում․ մոդելը չի ուսուցանվում"), demo("Share note", "Поделиться", "Կիսվել նշումով"))
                        5 -> {
                            Text(text.activity, style = MaterialTheme.typography.titleLarge)
                            if (session.audit_log.isEmpty()) {
                                Text(text.activityEmpty)
                            } else {
                                session.audit_log.forEach { event ->
                                    Card(
                                        Modifier.fillMaxWidth(),
                                        shape = RoundedCornerShape(16.dp),
                                        border = BorderStroke(
                                            1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.38f)
                                        ),
                                        colors = CardDefaults.cardColors(contentColor=MaterialTheme.colorScheme.onSurface,
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

            }
            if (state.loading) CircularProgressIndicator()
            state.error?.let { Text("${extra.error}: ${it}", color = MaterialTheme.colorScheme.error) }
        }
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
internal fun VehicleFields(
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
    onLpg: (Boolean) -> Unit,
    language: AppLanguage = AppLanguage.EN
) {
    val makes = catalog.map { it.make }.distinct().sorted()
    val models = modelOptionsFor(catalog, make)
    val chassisOptions = chassisOptionsFor(catalog, make, model)
    val years = yearOptionsFor(catalog, make, model, chassis).map(Int::toString)
    val engines = engineOptionsFor(catalog, make, model, chassis, year.toIntOrNull())
    val ecus = ecuOptionsFor(catalog, make, model, chassis, engine, year.toIntOrNull())

    if (model in models && chassis in chassisOptions) {
        VehicleModelArtwork(make, model, chassis)
    }
    VehicleSelectionField(text.make, make, makes, onMake)
    VehicleSelectionField(text.model, model, models, onModel)
    VehicleSelectionField(text.chassis, chassis, chassisOptions, onChassis)
    VehicleSelectionField(text.year, year, years, onYear)
    VehicleSelectionField(text.engine, engine, engines, onEngine)
    VehicleSelectionField(text.extra.ecu, ecu, ecus, onEcu)

    val serverFuel = catalog.firstOrNull { it.make == make && it.model == model && it.chassis == chassis && it.engine == engine }?.fuel.orEmpty()
    Text(text.fuel, style = MaterialTheme.typography.titleMedium)
    if (serverFuel.any { it.lowercase() !in listOf("petrol", "lpg") }) {
        Text(serverFuel.joinToString(" + ") { code -> when(code.lowercase()) {
            "diesel" -> when(language) { AppLanguage.RU -> "Дизель"; AppLanguage.HY -> "Դիզել"; else -> "Diesel" }
            "hybrid" -> when(language) { AppLanguage.RU -> "Гибрид"; AppLanguage.HY -> "Հիբրիդ"; else -> "Hybrid" }
            "electric" -> when(language) { AppLanguage.RU -> "Электрический"; AppLanguage.HY -> "Էլեկտրական"; else -> "Electric" }
            else -> code
        } })
    } else {
        Row { Checkbox(checked = petrol, onCheckedChange = onPetrol); Text(text.petrol) }
        Row { Checkbox(checked = lpg, onCheckedChange = onLpg); Text(text.lpg) }
    }
    if (catalog.any { it.scope == "generation-reference-not-vin-fitment" }) {
        Text(when(language) {
            AppLanguage.RU -> "Варианты двигателя зависят от года и рынка. Проверьте VIN и ЭБУ."
            AppLanguage.HY -> "Շարժիչը կախված է տարեթվից ու շուկայից։ Ստուգեք VIN-ը և ECU-ն։"
            else -> "Engine options vary by year and market. Confirm VIN and ECU."
        }, style=MaterialTheme.typography.bodySmall, color=MaterialTheme.colorScheme.onSurfaceVariant)
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
                .menuAnchor(MenuAnchorType.PrimaryNotEditable),
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
    MaterialTheme(colorScheme=if(settings.darkTheme) AutomotiveDarkColors else AutomotiveLightColors) {
        androidx.compose.ui.window.Dialog(onDismissRequest=onClose,properties=androidx.compose.ui.window.DialogProperties(usePlatformDefaultWidth=false)) {
            Surface(Modifier.fillMaxSize(),color=MaterialTheme.colorScheme.background) {
                Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),verticalArrangement=Arrangement.spacedBy(18.dp)) {
                    Row(verticalAlignment=androidx.compose.ui.Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                        TextButton(onClick=onClose) {Text("‹",style=MaterialTheme.typography.headlineMedium)}
                        Text(text.settings,style=MaterialTheme.typography.titleLarge,fontWeight=FontWeight.Bold)
                    }
                    DemoPanel(text.theme) {
                        Row(Modifier.fillMaxWidth(),verticalAlignment=androidx.compose.ui.Alignment.CenterVertically) {
                            DashboardIcon(12)
                            Column(Modifier.weight(1f).padding(start=14.dp)) {
                                Text(text.appearance,fontWeight=FontWeight.SemiBold)
                                Text(if(settings.darkTheme) text.dark else text.light,style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            androidx.compose.material3.Switch(checked=settings.darkTheme,onCheckedChange={onSettingsChanged(settings.copy(darkTheme=it))})
                        }
                    }
                    DemoPanel(dashboardLabel("Widget display")) {
                        Column {
                            FilterChip(selected=settings.analogDisplay,onClick={onSettingsChanged(settings.copy(analogDisplay=true))},label={Text(dashboardLabel("Analog gauge"))})
                            FilterChip(selected=!settings.analogDisplay,onClick={onSettingsChanged(settings.copy(analogDisplay=false))},label={Text(dashboardLabel("Line chart"))})
                        }
                    }
                    DemoPanel(dashboardLabel("Units")) {
                        Column(verticalArrangement=Arrangement.spacedBy(8.dp)) {
                            FilterChip(selected=!settings.usUnits,onClick={onSettingsChanged(settings.copy(usUnits=false))},label={Text("EU • km/h • °C")})
                            FilterChip(selected=settings.usUnits,onClick={onSettingsChanged(settings.copy(usUnits=true))},label={Text("USA • mph • °F")})
                        }
                    }
                    DemoPanel(text.language) {
                        listOf(AppLanguage.HY to "Հայերեն",AppLanguage.RU to "Русский",AppLanguage.EN to "English").forEach { (language,label) ->
                            androidx.compose.material3.OutlinedCard(onClick={onSettingsChanged(settings.copy(language=language));onLanguageChanged(language)},modifier=Modifier.fillMaxWidth(),shape=RoundedCornerShape(12.dp),border=BorderStroke(1.dp,if(settings.language==language) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outline.copy(alpha=.3f))) {
                                Row(Modifier.fillMaxWidth().padding(12.dp),verticalAlignment=androidx.compose.ui.Alignment.CenterVertically,horizontalArrangement=Arrangement.SpaceBetween) {
                                    Text(label,fontWeight=FontWeight.Medium)
                                    androidx.compose.material3.RadioButton(selected=settings.language==language,onClick=null)
                                }
                            }
                        }
                    }
                    Text(dashboardLabel("Preferences saved on this device"),color=MaterialTheme.colorScheme.onSurfaceVariant,style=MaterialTheme.typography.bodySmall)
                    Button(onClick=onClose,modifier=Modifier.fillMaxWidth()) {Text(text.close)}
                }
            }
        }
    }
}


/** Generated portraits use an exact catalog key and native image rendering. */
@Composable
internal fun VehicleModelArtwork(make: String, model: String, chassis: String, height: androidx.compose.ui.unit.Dp = 170.dp) {
    fun keyPart(value: String): String = value.lowercase(java.util.Locale.ROOT)
        .replace(Regex("[^a-z0-9]+"), "-").trim('-')
    val file = "vehicle_models/" +
        listOf(make, model, chassis).joinToString("_", transform = ::keyPart) + ".png"
    val context = LocalContext.current
    val sample = if (height <= 72.dp) 4 else 1
    val key = "$file/$sample"
    // Reset the displayed bitmap when the asset changes, including cached portraits.
    var portrait by remember(key) { mutableStateOf(vehiclePortraitCache.get(key)) }
    var photoCredit by remember(key) { mutableStateOf(vehicleCreditCache.get(key)) }
    LaunchedEffect(key) {
        if (portrait == null) {
            // Show the bundled cache immediately while requesting backend artwork.
            portrait = withContext(Dispatchers.IO) {
                runCatching { context.assets.open(file).use { stream ->
                    BitmapFactory.decodeStream(stream,null,BitmapFactory.Options().apply { inSampleSize=sample })?.asImageBitmap()
                } }.getOrNull()
            }
            val remote = withContext(Dispatchers.IO) {
                runCatching {
                    val query = listOf("make" to make, "model" to model, "chassis" to chassis).joinToString("&") { (name, value) -> name + "=" + java.net.URLEncoder.encode(value, "UTF-8") }
                    val connection = java.net.URL(com.aicarscaner.mobile.data.api.ApiClient.BASE_URL + "api/v1/vehicle-reference/image?" + query).openConnection().apply { connectTimeout=4000; readTimeout=4000 }
                    val bitmap = connection.getInputStream().use { input -> BitmapFactory.decodeStream(input,null,BitmapFactory.Options().apply { inSampleSize=sample })?.asImageBitmap() }
                    val author = java.net.URLDecoder.decode(connection.getHeaderField("X-Image-Credit") ?: "", "UTF-8")
                    val license = connection.getHeaderField("X-Image-License") ?: ""
                    val credit = listOf(author, license).filter { it.isNotBlank() }.joinToString(" • ")
                    Triple(bitmap, credit, connection.getHeaderField("X-Image-Source") ?: "")
                }.getOrNull()
            }
            if (remote?.first != null) {
                portrait = remote.first
                photoCredit = remote.second to remote.third
                vehicleCreditCache.put(key, photoCredit!!)
            }
            portrait?.let { vehiclePortraitCache.put(key,it) }
        }
    }

    if (portrait != null) {
        Image(
            bitmap = portrait,
            contentDescription = "$make $model $chassis",
            contentScale = ContentScale.Fit,
            modifier = Modifier.fillMaxWidth().height(height)
        )
        photoCredit?.takeIf { it.first.isNotBlank() }?.let { credit ->
            TextButton(onClick = {
                val uri = android.net.Uri.parse(credit.second)
                if (uri.scheme == "https" && uri.host == "commons.wikimedia.org") {
                    context.startActivity(android.content.Intent(android.content.Intent.ACTION_VIEW, uri))
                }
            }) { Text(credit.first, style=MaterialTheme.typography.labelSmall, maxLines=2) }
        }
    } else {
        androidx.compose.foundation.layout.Box(Modifier.fillMaxWidth().height(height),contentAlignment=androidx.compose.ui.Alignment.Center) {
            DashboardIcon(6,Modifier.size(if(height<=72.dp) 32.dp else 64.dp),MaterialTheme.colorScheme.primary.copy(alpha=.45f))
        }
    }
}

private val vehiclePortraitCache = object : android.util.LruCache<String, androidx.compose.ui.graphics.ImageBitmap>(24 * 1024 * 1024) {
    override fun sizeOf(key: String, value: androidx.compose.ui.graphics.ImageBitmap): Int = value.width * value.height * 4
}

private val vehicleCreditCache = android.util.LruCache<String, Pair<String, String>>(96)

internal fun formFuel(catalog: List<VehicleCatalogEntryDto>, make: String, model: String, chassis: String, engine: String, petrol: Boolean, lpg: Boolean): List<String> {
    val provided = catalog.firstOrNull { it.make == make && it.model == model && it.chassis == chassis && it.engine == engine }?.fuel.orEmpty()
    return if (provided.any { it.lowercase() !in listOf("petrol", "lpg") }) provided
    else buildList { if (petrol) add("petrol"); if (lpg) add("LPG") }
}
