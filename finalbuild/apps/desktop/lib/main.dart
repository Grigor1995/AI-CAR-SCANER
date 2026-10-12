import 'dart:async';
import 'dart:math' as math;

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api_client.dart';
import 'models.dart';
import 'vehicle_catalog.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const DiagnosticDesktopApp());
}

class DiagnosticDesktopApp extends StatelessWidget {
  const DiagnosticDesktopApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI Auto Diagnostic Workstation',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0B0F14),
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF5DA9FF), brightness: Brightness.dark),
        cardTheme: CardTheme(
          elevation: 0,
          color: const Color(0xFF111720),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: const Color(0xFF0F141C),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide.none),
        ),
      ),
      home: const DesktopShell(),
    );
  }
}

class DesktopShell extends StatefulWidget {
  const DesktopShell({super.key});

  @override
  State<DesktopShell> createState() => _DesktopShellState();
}

class _DesktopShellState extends State<DesktopShell> {
  final DiagnosticApiClient api = DiagnosticApiClient();
  final List<String> pages = const ['Dashboard', 'Vehicles', 'Diagnostic', 'Live Data', 'ECU Network', 'Tests', 'Reports', 'Settings'];

  int selectedIndex = 0;
  bool online = false;
    String? error;

  List<VehicleModel> vehicles = [];
  List<Map<String, dynamic>> catalogEntries = [];
  VehicleModel? activeVehicle;
  DiagnosticSessionModel? activeSession;
  Map<String, dynamic> sessionJson = {};
  Map<String, dynamic> decisionJson = {};
  Map<String, dynamic> telemetryJson = {};
  Map<String, dynamic> networkJson = {};
  Map<String, List<double>> liveSeries = {};
  bool acquisitionRunning = false;

  Timer? poller;

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  @override
  void dispose() {
    poller?.cancel();
    super.dispose();
  }

  Future<void> _bootstrap() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getStringList('vehicle_profiles') ?? <String>[];
    vehicles = raw.map((line) {
      final parts = line.split('|');
      final legacy = parts.length < 7;
      return VehicleModel(
        make: parts.isNotEmpty ? parts[0] : 'Vehicle',
        model: parts.length > 1 ? parts[1] : 'Profile',
        chassis: legacy ? '' : parts[2],
        year: legacy ? (parts.length > 2 ? int.tryParse(parts[2]) : null) : int.tryParse(parts[3]),
        engine: legacy ? (parts.length > 3 ? parts[3] : null) : parts[4],
        fuel: (legacy ? (parts.length > 4 ? parts[4] : '') : (parts.length > 5 ? parts[5] : '')).split(',').where((x) => x.isNotEmpty).toList(),
        ecu: legacy ? '' : (parts.length > 6 ? parts[6] : ''),
      );
    }).toList();
    try {
      catalogEntries = await api.catalogEntries();
    } catch (_) {
      // Keep the bundled catalog as an offline/demo fallback. The shared DB
      // remains authoritative whenever the backend is available.
      catalogEntries = [];
    }
    await refreshHealth();
  }

  Future<void> refreshHealth() async {
    final result = await api.health();
    if (!mounted) return;
    setState(() {
      online = result;
      error = result ? null : 'Backend API is offline. Desktop stays usable in local/demo mode.';
    });
  }

  Future<void> createSession(VehicleModel vehicle) async {
    try {
      final json = await api.createSession(vehicle: vehicle.toJson());
      final session = DiagnosticSessionModel.fromJson(json);
      if (!mounted) return;
      setState(() {
        activeVehicle = vehicle;
        activeSession = session;
        sessionJson = json;
        selectedIndex = 2;
        error = null;
      });
      _startPolling();
      _snack('Diagnostic session created');
    } on DioException catch (e) {
      _showError(_dioMessage(e));
    }
  }

  Future<void> saveVehicle(VehicleModel vehicle) async {
    final prefs = await SharedPreferences.getInstance();
    final merged = [...vehicles, vehicle];
    final deduped = <String, VehicleModel>{for (final v in merged) '${v.make}|${v.model}|${v.chassis}|${v.year}|${v.engine}|${v.ecu}': v}.values.toList();
    vehicles = deduped;
    await prefs.setStringList('vehicle_profiles', vehicles.map((v) => '${v.make}|${v.model}|${v.chassis}|${v.year ?? ''}|${v.engine ?? ''}|${v.fuel.join(',')}|${v.ecu}').toList());
    if (!mounted) return;
    setState(() {});
    await createSession(vehicle);
  }

  void _startPolling() {
    poller?.cancel();
    if (activeSession == null) return;
    poller = Timer.periodic(const Duration(seconds: 2), (_) async {
      if (!mounted || activeSession == null || !online) return;
      await _refreshSessionData(silent: true);
    });
  }

  Future<void> _refreshSessionData({bool silent = false}) async {
    final session = activeSession;
    if (session == null || !online) return;
    try {
      final sessionData = await api.getSession(session.id);
      final plan = await api.decisionPlan(session.id);
      final telemetry = await api.telemetrySummary(session.id);
      final records = await api.acquisitionRecords(session.id);
      final nextSeries = <String, List<double>>{};
      for (final record in records) {
        final value = (record['numeric_value'] as num?)?.toDouble();
        final channel = record['channel']?.toString();
        if (value != null && channel != null) {
          (nextSeries[channel] ??= <double>[]).add(value);
        }
      }
      if (!mounted) return;
      setState(() {
        sessionJson = sessionData;
        activeSession = DiagnosticSessionModel.fromJson(sessionData);
        decisionJson = plan;
        telemetryJson = telemetry;
        liveSeries = nextSeries;
      });
    } catch (e) {
      if (!silent && mounted) _showError(e.toString());
    }
  }

  Future<void> ingestAndAnalyze(String text) async {
    final id = activeSession?.id;
    if (id == null || !online) {
      _showError('Create a session and start the backend first.');
      return;
    }
    try {
      await api.ingestEvidence(id, text);
      final result = await api.analyze(id);
      final plan = await api.decisionPlan(id);
      if (!mounted) return;
      setState(() {
        sessionJson = result;
        activeSession = DiagnosticSessionModel.fromJson(result);
        decisionJson = plan;
      });
      _snack('Evidence analyzed and diagnostic plan updated');
    } on DioException catch (e) {
      _showError(_dioMessage(e));
    }
  }

  Future<void> addDtc(String code) async {
    final id = activeSession?.id;
    if (id == null || !online) {
      _showError('Create a session and start the backend first.');
      return;
    }
    try {
      final result = await api.addDtc(id, code.trim());
      if (!mounted) return;
      setState(() {
        sessionJson = result;
        activeSession = DiagnosticSessionModel.fromJson(result);
      });
      _snack('DTC $code added to session');
    } on DioException catch (e) {
      _showError(_dioMessage(e));
    }
  }

  Future<void> addSymptom(String text) async {
    final id = activeSession?.id;
    if (id == null || !online || text.trim().isEmpty) {
      _showError('Create a session and enter a symptom first.');
      return;
    }
    try {
      final updated = await api.addSymptom(id, text.trim());
      if (!mounted) return;
      setState(() {
        sessionJson = updated;
        activeSession = DiagnosticSessionModel.fromJson(updated);
      });
      _snack('Symptom added');
    } on DioException catch (e) {
      _showError(_dioMessage(e));
    }
  }

  Future<void> updateSymptom(String symptomId, String text) async {
    final id = activeSession?.id;
    if (id == null || !online || text.trim().isEmpty) return;
    try {
      final updated = await api.updateSymptom(id, symptomId, text.trim());
      if (!mounted) return;
      setState(() {
        sessionJson = updated;
        activeSession = DiagnosticSessionModel.fromJson(updated);
      });
      _snack('Symptom updated');
    } on DioException catch (e) {
      _showError(_dioMessage(e));
    }
  }

  Future<void> deleteSymptom(String symptomId) async {
    final id = activeSession?.id;
    if (id == null || !online) return;
    try {
      final updated = await api.deleteSymptom(id, symptomId);
      if (!mounted) return;
      setState(() {
        sessionJson = updated;
        activeSession = DiagnosticSessionModel.fromJson(updated);
      });
      _snack('Symptom deleted');
    } on DioException catch (e) {
      _showError(_dioMessage(e));
    }
  }

  Future<void> updateDtc(String dtcId, String code, String? description, String? source) async {
    final id = activeSession?.id;
    if (id == null || !online || code.trim().isEmpty) return;
    try {
      final updated = await api.updateDtc(id, dtcId, code.trim(), description: description, source: source);
      if (!mounted) return;
      setState(() {
        sessionJson = updated;
        activeSession = DiagnosticSessionModel.fromJson(updated);
      });
      _snack('DTC updated');
    } on DioException catch (e) {
      _showError(_dioMessage(e));
    }
  }

  Future<void> deleteDtc(String dtcId) async {
    final id = activeSession?.id;
    if (id == null || !online) return;
    try {
      final updated = await api.deleteDtc(id, dtcId);
      if (!mounted) return;
      setState(() {
        sessionJson = updated;
        activeSession = DiagnosticSessionModel.fromJson(updated);
      });
      _snack('DTC deleted');
    } on DioException catch (e) {
      _showError(_dioMessage(e));
    }
  }

  Future<void> recordTestResult(TestCandidateModel candidate, String result, String notes) async {
    final id = activeSession?.id;
    if (id == null || !online) {
      _showError('Create a session and connect to the backend first.');
      return;
    }
    try {
      final updated = await api.recordTestResult(id, candidate.id, result, notes: notes);
      final plan = await api.decisionPlan(id);
      if (!mounted) return;
      setState(() {
        sessionJson = updated;
        activeSession = DiagnosticSessionModel.fromJson(updated);
        decisionJson = plan;
      });
      _snack('Test result recorded: $result');
    } on DioException catch (e) {
      _showError(_dioMessage(e));
    }
  }

  Future<void> toggleAcquisition() async {
    final id = activeSession?.id;
    if (id == null || !online) {
      _showError('Create a session and make sure the FastAPI backend is running.');
      return;
    }
    try {
      if (!acquisitionRunning) {
        await api.startSimulator(id);
        acquisitionRunning = true;
        _snack('Simulator live-data acquisition started');
      } else {
        await api.stopAcquisition(id);
        acquisitionRunning = false;
        _snack('Live-data acquisition stopped');
      }
      if (mounted) setState(() {});
      await _refreshSessionData();
    } on DioException catch (e) {
      _showError(_dioMessage(e));
    }
  }

  Future<void> loadDemoNetwork() async {
    final id = activeSession?.id;
    if (id == null || !online) {
      _showError('Create a session and make sure the backend is running.');
      return;
    }
    try {
      await api.ingestCanFrames(id, 'CAN0', [
        {'arbitration_id': 0x7E0, 'data_hex': '022201F190', 'is_extended': false, 'is_fd': false},
        {'arbitration_id': 0x7E8, 'data_hex': '104B62F190574442323131303030303030303030303031', 'is_extended': false, 'is_fd': false},
        {'arbitration_id': 0x7E8, 'data_hex': '213030312020202020202020202020202020202020202020', 'is_extended': false, 'is_fd': false},
        {'arbitration_id': 0x7E1, 'data_hex': '02190202', 'is_extended': false, 'is_fd': false},
        {'arbitration_id': 0x7E9, 'data_hex': '06596202400131', 'is_extended': false, 'is_fd': false},
      ]);
      networkJson = await api.networkDiscovery(id);
      if (!mounted) return;
      setState(() {});
      _snack('Demo CAN traffic discovered and mapped');
    } on DioException catch (e) {
      _showError(_dioMessage(e));
    }
  }

  String _dioMessage(DioException e) => e.response?.data is Map
      ? (e.response?.data['detail']?.toString() ?? 'API request failed')
      : e.message ?? 'API request failed';

  void _showError(String message) {
    if (!mounted) return;
    setState(() => error = message);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }

  void _snack(String message) => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            minWidth: 92,
            extended: MediaQuery.sizeOf(context).width > 1250,
            selectedIndex: selectedIndex,
            onDestinationSelected: (value) => setState(() => selectedIndex = value),
            backgroundColor: const Color(0xFF090D12),
            leading: Padding(
              padding: const EdgeInsets.symmetric(vertical: 18),
              child: Icon(Icons.electric_car, color: Theme.of(context).colorScheme.primary, size: 32),
            ),
            destinations: pages.map((page) => NavigationRailDestination(icon: _iconFor(page), label: Text(page))).toList(),
          ),
          const VerticalDivider(width: 1),
          Expanded(
            child: Column(
              children: [
                _TopBar(online: online, session: activeSession, onRefresh: refreshHealth),
                if (error != null) _StatusBanner(message: error!, onClose: () => setState(() => error = null)),
                Expanded(child: _pageFor(selectedIndex)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Icon _iconFor(String page) {
    switch (page) {
      case 'Dashboard': return const Icon(Icons.dashboard_outlined);
      case 'Vehicles': return const Icon(Icons.directions_car_outlined);
      case 'Diagnostic': return const Icon(Icons.health_and_safety_outlined);
      case 'Live Data': return const Icon(Icons.monitor_heart_outlined);
      case 'ECU Network': return const Icon(Icons.account_tree_outlined);
      case 'Tests': return const Icon(Icons.rule_folder_outlined);
      case 'Reports': return const Icon(Icons.description_outlined);
      default: return const Icon(Icons.settings_outlined);
    }
  }

  Widget _pageFor(int index) {
    switch (index) {
      case 0:
        return DashboardPage(
          online: online,
          vehicle: activeVehicle,
          session: activeSession,
          telemetry: telemetryJson,
          onNewSession: () => setState(() => selectedIndex = 1),
          onDiagnostic: () => setState(() => selectedIndex = 2),
        );
      case 1:
        return VehiclesPage(catalog: catalogEntries, vehicles: vehicles, onCreateSession: createSession, onSaveVehicle: saveVehicle);
      case 2:
        return DiagnosticPage(
          session: activeSession,
          sessionJson: sessionJson,
          onAnalyze: ingestAndAnalyze,
          onAddDtc: addDtc,
          onAddSymptom: addSymptom,
          onUpdateSymptom: updateSymptom,
          onDeleteSymptom: deleteSymptom,
          onUpdateDtc: updateDtc,
          onDeleteDtc: deleteDtc,
          onOpenTests: () => setState(() => selectedIndex = 5),
        );
      case 3:
        return LiveDataPage(
          session: activeSession,
          acquisitionRunning: acquisitionRunning,
          telemetry: telemetryJson,
          liveSeries: liveSeries,
          onToggleAcquisition: toggleAcquisition,
          onRefresh: _refreshSessionData,
        );
      case 4:
        return NetworkPage(session: activeSession, network: networkJson, onDemo: loadDemoNetwork);
      case 5:
        return TestsPage(session: activeSession, decision: decisionJson, onRefresh: _refreshSessionData, onRecordTest: recordTestResult);
      case 6:
        return ReportsPage(session: activeSession, sessionJson: sessionJson, telemetry: telemetryJson);
      default:
        return SettingsPage(online: online, apiUrl: const String.fromEnvironment('API_URL', defaultValue: 'http://127.0.0.1:8000'));
    }
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar({required this.online, required this.session, required this.onRefresh});
  final bool online;
  final DiagnosticSessionModel? session;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 72,
      padding: const EdgeInsets.symmetric(horizontal: 26),
      decoration: const BoxDecoration(color: Color(0xFF0D1219), border: Border(bottom: BorderSide(color: Color(0xFF202832)))),
      child: Row(
        children: [
          const Text('AI AUTO DIAGNOSTIC', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800, letterSpacing: 1.3)),
          const Spacer(),
          if (session != null) ...[
            Chip(avatar: const Icon(Icons.bolt, size: 16), label: Text('SESSION ${session!.id.substring(0, 8)}')),
            const SizedBox(width: 10),
          ],
          Chip(
            avatar: Icon(online ? Icons.cloud_done : Icons.cloud_off, size: 16),
            label: Text(online ? 'API ONLINE' : 'OFFLINE'),
          ),
          const SizedBox(width: 10),
          IconButton(tooltip: 'Refresh backend', onPressed: onRefresh, icon: const Icon(Icons.refresh)),
        ],
      ),
    );
  }
}

class _StatusBanner extends StatelessWidget {
  const _StatusBanner({required this.message, required this.onClose});
  final String message;
  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) => MaterialBanner(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
        backgroundColor: const Color(0xFF2A2011),
        content: Text(message),
        leading: const Icon(Icons.info_outline),
        actions: [TextButton(onPressed: onClose, child: const Text('Dismiss'))],
      );
}

class DashboardPage extends StatelessWidget {
  const DashboardPage({super.key, required this.online, this.vehicle, this.session, required this.telemetry, required this.onNewSession, required this.onDiagnostic});
  final bool online;
  final VehicleModel? vehicle;
  final DiagnosticSessionModel? session;
  final Map<String, dynamic> telemetry;
  final VoidCallback onNewSession;
  final VoidCallback onDiagnostic;

  @override
  Widget build(BuildContext context) {
    final sampleCount = (telemetry['sample_count'] as num?)?.toInt() ?? 0;
    return ListView(
      padding: const EdgeInsets.all(26),
      children: [
        Text('Workshop Dashboard', style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800)),
        const SizedBox(height: 6),
        Text('Evidence-driven diagnostics for desktop workshops', style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: Colors.white60)),
        const SizedBox(height: 24),
        Wrap(spacing: 14, runSpacing: 14, children: [
          _MetricCard(title: 'System', value: online ? 'Ready' : 'Offline', caption: 'FastAPI diagnostic engine', icon: online ? Icons.check_circle_outline : Icons.cloud_off),
          _MetricCard(title: 'Vehicle', value: vehicle == null ? '—' : '${vehicle!.make} ${vehicle!.model}', caption: vehicle?.engine ?? 'No active profile', icon: Icons.directions_car_outlined),
          _MetricCard(title: 'Session', value: session == null ? '—' : session!.state, caption: session == null ? 'Create a diagnostic session' : session!.id.substring(0, 12), icon: Icons.health_and_safety_outlined),
          _MetricCard(title: 'Telemetry', value: '$sampleCount', caption: 'samples collected', icon: Icons.monitor_heart_outlined),
        ]),
        const SizedBox(height: 24),
        Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(child: _ActionCard(
            title: 'Start a Diagnostic Session',
            description: 'Select a vehicle, enter symptoms and DTCs, run AI-assisted analysis, and follow recommended tests.',
            action: FilledButton.icon(onPressed: onNewSession, icon: const Icon(Icons.add), label: const Text('New Session')),
          )),
          const SizedBox(width: 16),
          Expanded(child: _ActionCard(
            title: 'Continue Current Session',
            description: session == null ? 'No active session yet.' : 'Continue evidence collection and review diagnostic hypotheses.',
            action: FilledButton.icon(onPressed: session == null ? null : onDiagnostic, icon: const Icon(Icons.play_arrow), label: const Text('Open Diagnostic')),
          )),
        ]),
      ],
    );
  }
}

class VehiclesPage extends StatefulWidget {
  const VehiclesPage({
    super.key,
    required this.catalog,
    required this.vehicles,
    required this.onCreateSession,
    required this.onSaveVehicle,
  });

  final List<Map<String, dynamic>> catalog;
  final List<VehicleModel> vehicles;
  final Future<void> Function(VehicleModel vehicle) onCreateSession;
  final Future<void> Function(VehicleModel vehicle) onSaveVehicle;

  @override
  State<VehiclesPage> createState() => _VehiclesPageState();
}

class _VehiclesPageState extends State<VehiclesPage> {
  String make = 'Mercedes-Benz';
  String model = 'E-Class';
  String chassis = 'W211';
  int? year = 2006;
  String engine = 'M272 E35 3.5';
  String ecu = 'ME9.7';
  final fuel = TextEditingController(text: 'Petrol,LPG');

  List<Map<String, dynamic>> get _catalog => widget.catalog;

  List<Map<String, dynamic>> _filtered({
    String? selectedMake,
    String? selectedModel,
    String? selectedChassis,
    int? selectedYear,
    String? selectedEngine,
  }) {
    Iterable<Map<String, dynamic>> rows = _catalog;
    if (selectedMake != null) rows = rows.where((x) => x['make']?.toString() == selectedMake);
    if (selectedModel != null) rows = rows.where((x) => x['model']?.toString() == selectedModel);
    if (selectedChassis != null && selectedChassis.isNotEmpty) rows = rows.where((x) => x['chassis']?.toString() == selectedChassis);
    if (selectedYear != null) rows = rows.where((x) => (x['year'] as num?)?.toInt() == selectedYear);
    if (selectedEngine != null) rows = rows.where((x) => x['engine']?.toString() == selectedEngine);
    return rows.toList();
  }

  List<String> _makes() {
    if (_catalog.isEmpty) return vehicleCatalog.map((x) => x.name).toList();
    return _catalog.map((x) => x['make']?.toString()).whereType<String>().toSet().toList()..sort();
  }

  List<String> _models() {
    if (_catalog.isEmpty) return findMake(make)?.models.map((x) => x.name).toList() ?? [];
    return _filtered(selectedMake: make).map((x) => x['model']?.toString()).whereType<String>().toSet().toList()..sort();
  }

  List<String> _chassisOptions() {
    if (_catalog.isEmpty) return findModel(make, model)?.chassisOptions.map((x) => x.chassis).toList() ?? [];
    return _filtered(selectedMake: make, selectedModel: model)
        .map((x) => x['chassis']?.toString()).whereType<String>().toSet().toList()..sort();
  }

  List<int> _years() {
    if (_catalog.isEmpty) return findChassis(make, model, chassis)?.years ?? [];
    return _filtered(selectedMake: make, selectedModel: model, selectedChassis: chassis)
        .map((x) => (x['year'] as num?)?.toInt()).whereType<int>().toSet().toList()..sort((a,b) => b.compareTo(a));
  }

  List<String> _engines() {
    if (_catalog.isEmpty) return findChassis(make, model, chassis)?.engines.map((x) => x.name).toList() ?? [];
    return _filtered(selectedMake: make, selectedModel: model, selectedChassis: chassis, selectedYear: year)
        .map((x) => x['engine']?.toString()).whereType<String>().toSet().toList()..sort();
  }

  List<String> _ecus() {
    if (_catalog.isEmpty) return findChassis(make, model, chassis)
        ?.engines.firstWhere((x) => x.name == engine, orElse: () => findChassis(make, model, chassis)!.engines.first)
        .ecus ?? [];
    return _filtered(
      selectedMake: make,
      selectedModel: model,
      selectedChassis: chassis,
      selectedYear: year,
      selectedEngine: engine,
    ).map((x) => x['ecu']?.toString()).whereType<String>().toSet().toList()..sort();
  }

  void _selectMake(String value) {
    if (_catalog.isEmpty) {
      final m = findMake(value) ?? vehicleCatalog.first;
      final mo = m.models.first; final ch = mo.chassisOptions.first; final en = ch.engines.first;
      setState(() { make=m.name; model=mo.name; chassis=ch.chassis; year=ch.years.first; engine=en.name; ecu=en.ecus.first; });
      return;
    }
    final models = _filtered(selectedMake: value).map((x) => x['model']?.toString()).whereType<String>().toSet().toList()..sort();
    if (models.isEmpty) return;
    _selectModel(models.first, makeValue: value);
  }

  void _selectModel(String value, {String? makeValue}) {
    final selectedMake = makeValue ?? make;
    if (_catalog.isEmpty) {
      final mo = findModel(selectedMake, value) ?? findMake(selectedMake)!.models.first;
      final ch = mo.chassisOptions.first; final en = ch.engines.first;
      setState(() { make=selectedMake; model=mo.name; chassis=ch.chassis; year=ch.years.first; engine=en.name; ecu=en.ecus.first; });
      return;
    }
    final rows = _filtered(selectedMake: selectedMake, selectedModel: value);
    final chassisValues = rows.map((x) => x['chassis']?.toString()).whereType<String>().toSet().toList()..sort();
    if (chassisValues.isEmpty) return;
    final nextChassis = chassisValues.first;
    final years = _filtered(selectedMake: selectedMake, selectedModel: value, selectedChassis: nextChassis)
        .map((x) => (x['year'] as num?)?.toInt()).whereType<int>().toSet().toList()..sort((a,b) => b.compareTo(a));
    if (years.isEmpty) return;
    final nextYear = years.contains(2006) ? 2006 : years.first;
    final engines = _filtered(selectedMake: selectedMake, selectedModel: value, selectedChassis: nextChassis, selectedYear: nextYear)
        .map((x) => x['engine']?.toString()).whereType<String>().toSet().toList()..sort();
    if (engines.isEmpty) return;
    final nextEngine = engines.first;
    final ecus = _filtered(selectedMake: selectedMake, selectedModel: value, selectedChassis: nextChassis, selectedYear: nextYear, selectedEngine: nextEngine)
        .map((x) => x['ecu']?.toString()).whereType<String>().toSet().toList()..sort();
    setState(() { make=selectedMake; model=value; chassis=nextChassis; year=nextYear; engine=nextEngine; ecu=ecus.isEmpty ? '' : ecus.first; });
  }

  void _selectChassis(String value) {
    if (_catalog.isEmpty) {
      final ch = findChassis(make, model, value) ?? findModel(make, model)!.chassisOptions.first;
      final en = ch.engines.first;
      setState(() { chassis=ch.chassis; year=ch.years.first; engine=en.name; ecu=en.ecus.first; });
      return;
    }
    final years = _filtered(selectedMake: make, selectedModel: model, selectedChassis: value)
        .map((x) => (x['year'] as num?)?.toInt()).whereType<int>().toSet().toList()..sort((a,b) => b.compareTo(a));
    if (years.isEmpty) return;
    final nextYear = years.first;
    final engines = _filtered(selectedMake: make, selectedModel: model, selectedChassis: value, selectedYear: nextYear)
        .map((x) => x['engine']?.toString()).whereType<String>().toSet().toList()..sort();
    if (engines.isEmpty) return;
    final nextEngine = engines.first;
    final ecus = _filtered(selectedMake: make, selectedModel: model, selectedChassis: value, selectedYear: nextYear, selectedEngine: nextEngine)
        .map((x) => x['ecu']?.toString()).whereType<String>().toSet().toList()..sort();
    setState(() { chassis=value; year=nextYear; engine=nextEngine; ecu=ecus.isEmpty ? '' : ecus.first; });
  }

  void _selectYear(int value) {
    if (_catalog.isEmpty) {
      setState(() => year=value);
      return;
    }
    final engines = _filtered(selectedMake: make, selectedModel: model, selectedChassis: chassis, selectedYear: value)
        .map((x) => x['engine']?.toString()).whereType<String>().toSet().toList()..sort();
    if (engines.isEmpty) return;
    final nextEngine = engines.contains(engine) ? engine : engines.first;
    final ecus = _filtered(selectedMake: make, selectedModel: model, selectedChassis: chassis, selectedYear: value, selectedEngine: nextEngine)
        .map((x) => x['ecu']?.toString()).whereType<String>().toSet().toList()..sort();
    setState(() { year=value; engine=nextEngine; ecu=ecus.isEmpty ? '' : ecus.first; });
  }

  void _selectEngine(String value) {
    if (_catalog.isEmpty) {
      final ch = findChassis(make, model, chassis)!;
      final en = ch.engines.firstWhere((x)=>x.name==value,orElse:()=>ch.engines.first);
      setState(() { engine=en.name; ecu=en.ecus.first; });
      return;
    }
    final ecus = _filtered(selectedMake: make, selectedModel: model, selectedChassis: chassis, selectedYear: year, selectedEngine: value)
        .map((x) => x['ecu']?.toString()).whereType<String>().toSet().toList()..sort();
    setState(() { engine=value; ecu=ecus.isEmpty ? '' : ecus.first; });
  }

  VehicleModel get _formVehicle => VehicleModel(
    make: make,
    model: model,
    chassis: chassis,
    year: year,
    engine: engine,
    fuel: fuel.text.split(',').map((e)=>e.trim()).where((e)=>e.isNotEmpty).toList(),
    ecu: ecu,
  );

  @override
  void dispose() { fuel.dispose(); super.dispose(); }

  Widget _select(String label,String value,List<String> options,ValueChanged<String> onChanged)=>SizedBox(
    width:210, child:DropdownButtonFormField<String>(
      value:options.contains(value)?value:(options.isEmpty?null:options.first),
      decoration:InputDecoration(labelText:label),
      items:options.map((x)=>DropdownMenuItem(value:x,child:Text(x))).toList(),
      onChanged:options.isEmpty?null:(v){if(v!=null)onChanged(v);},
    ));

  @override
  Widget build(BuildContext context){
    final modelOptions=_models();
    final chassisOptions=_chassisOptions();
    final yearOptions=_years();
    final engineOptions=_engines();
    final ecuOptions=_ecus();
    return ListView(padding:const EdgeInsets.all(26),children:[
      _PageTitle(title:'Vehicles',subtitle:'Real-world Make → Model → Chassis → Year → Engine → ECU selection from the shared backend catalog.'),
      const SizedBox(height:20),
      Card(child:Padding(padding:const EdgeInsets.all(20),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        const Text('Create / select vehicle',style:TextStyle(fontSize:18,fontWeight:FontWeight.w700)),
        const SizedBox(height:16),
        Wrap(spacing:12,runSpacing:12,children:[
          _select('Manufacturer',make,_makes(),_selectMake),
          _select('Model',model,modelOptions,_selectModel),
          _select('Chassis',chassis,chassisOptions,_selectChassis),
          SizedBox(width:120,child:DropdownButtonFormField<int>(
            value:yearOptions.contains(year)?year:(yearOptions.isEmpty?null:yearOptions.first),
            decoration:const InputDecoration(labelText:'Year'),
            items:yearOptions.map((x)=>DropdownMenuItem(value:x,child:Text('$x'))).toList(),
            onChanged:yearOptions.isEmpty?null:(v){if(v!=null)_selectYear(v);},
          )),
          _select('Engine',engine,engineOptions,_selectEngine),
          SizedBox(width:210,child:DropdownButtonFormField<String>(
            value:ecuOptions.contains(ecu)?ecu:(ecuOptions.isEmpty?null:ecuOptions.first),
            decoration:const InputDecoration(labelText:'ECU'),
            items:ecuOptions.map((x)=>DropdownMenuItem(value:x,child:Text(x))).toList(),
            onChanged:ecuOptions.isEmpty?null:(v){if(v!=null)setState(()=>ecu=v);},
          )),
          SizedBox(width:220,child:TextField(controller:fuel,decoration:const InputDecoration(labelText:'Fuel modes'))),
        ]),
        const SizedBox(height:18),
        FilledButton.icon(
          onPressed:(_makes().isEmpty || modelOptions.isEmpty || chassisOptions.isEmpty || yearOptions.isEmpty || engineOptions.isEmpty)
              ? null
              : ()=>widget.onSaveVehicle(_formVehicle),
          icon:const Icon(Icons.add_circle_outline),
          label:const Text('Save & Start Session'),
        ),
      ]))),
      const SizedBox(height:18),
      if(widget.vehicles.isEmpty)const _EmptyState(icon:Icons.directions_car_outlined,title:'No saved vehicles',subtitle:'Add your first workshop vehicle above.'),
      ...widget.vehicles.map((v)=>Card(
        margin:const EdgeInsets.only(bottom:10),
        child:ListTile(
          leading:CircleAvatar(child:Text(v.make.isEmpty?'?':v.make.substring(0,1))),
          title:Text('${v.make} ${v.model} / ${v.chassis}${v.year==null?'':' • ${v.year}'}'),
          subtitle:Text('${v.engine??'Engine unknown'} • ECU ${v.ecu.isEmpty?'unknown':v.ecu} • ${v.fuel.isEmpty?'Fuel unknown':v.fuel.join(' + ')}'),
          trailing:FilledButton.tonal(onPressed:()=>widget.onCreateSession(v),child:const Text('Start Session')),
        ),
      )),
    ]);
  }
}

class DiagnosticPage extends StatefulWidget {
  const DiagnosticPage({super.key, this.session, required this.sessionJson, required this.onAnalyze, required this.onAddDtc, required this.onAddSymptom, required this.onUpdateSymptom, required this.onDeleteSymptom, required this.onUpdateDtc, required this.onDeleteDtc, required this.onOpenTests});
  final DiagnosticSessionModel? session;
  final Map<String, dynamic> sessionJson;
  final Future<void> Function(String text) onAnalyze;
  final Future<void> Function(String code) onAddDtc;
  final Future<void> Function(String text) onAddSymptom;
  final Future<void> Function(String symptomId, String text) onUpdateSymptom;
  final Future<void> Function(String symptomId) onDeleteSymptom;
  final Future<void> Function(String dtcId, String code) onUpdateDtc;
  final Future<void> Function(String dtcId) onDeleteDtc;
  final VoidCallback onOpenTests;

  @override
  State<DiagnosticPage> createState() => _DiagnosticPageState();
}

class _DiagnosticPageState extends State<DiagnosticPage> {
  final controller = TextEditingController(text: 'Engine shakes below 2000 RPM during acceleration on LPG; petrol operation is normal.');
  final dtcController = TextEditingController(text: 'P0302');
  final symptomController = TextEditingController();
  final editDtcController = TextEditingController();
  String? editingSymptomId;
  String? editingDtcId;
  bool busy = false;
  bool dtcBusy = false;

  @override
  void dispose() { controller.dispose(); dtcController.dispose(); symptomController.dispose(); editDtcController.dispose(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    final evidence = ((widget.sessionJson['evidence'] as List?) ?? const []).map((e) => EvidenceModel.fromJson(Map<String, dynamic>.from(e as Map))).toList();
    final hypotheses = ((widget.sessionJson['hypotheses'] as List?) ?? const []).map((e) => HypothesisModel.fromJson(Map<String, dynamic>.from(e as Map))).toList();
    final dtcs = ((widget.sessionJson['dtcs'] as List?) ?? const []).map((e) => Map<String, dynamic>.from(e as Map)).toList();
    final symptoms = ((widget.sessionJson['symptoms'] as List?) ?? const []).map((e) => Map<String, dynamic>.from(e as Map)).toList();

    return ListView(padding: const EdgeInsets.all(26), children: [
      _PageTitle(title: 'Diagnostic', subtitle: widget.session == null ? 'Create a session first.' : 'Current evidence, hypotheses and next actions.'),
      const SizedBox(height: 20),
      if (widget.session == null)
        const _EmptyState(icon: Icons.health_and_safety_outlined, title: 'No active diagnostic session', subtitle: 'Open Vehicles and start a session.')
      else ...[
        Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(child: Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Describe what you observe', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            const Text('Natural language is converted into structured evidence. The engine keeps provenance explicit.'),
            const SizedBox(height: 14),
            TextField(controller: controller, minLines: 4, maxLines: 7, decoration: const InputDecoration(hintText: 'Symptoms, conditions, measurements, what changed…')),
            const SizedBox(height: 12),
            Row(children: [
              SizedBox(width: 150, child: TextField(controller: dtcController, decoration: const InputDecoration(labelText: 'DTC'))),
              const SizedBox(width: 10),
              OutlinedButton.icon(onPressed: dtcBusy ? null : () async { if (dtcController.text.trim().isEmpty) return; setState(() => dtcBusy = true); await widget.onAddDtc(dtcController.text.trim().toUpperCase()); if (mounted) setState(() { dtcBusy = false; dtcController.clear(); }); }, icon: const Icon(Icons.add_alert_outlined), label: Text(dtcBusy ? 'Adding…' : 'Add DTC')),
            ]),
            const SizedBox(height: 14),
            Row(children: [
              FilledButton.icon(onPressed: busy ? null : () async { setState(() => busy = true); await widget.onAnalyze(controller.text); if (mounted) setState(() => busy = false); }, icon: const Icon(Icons.auto_awesome), label: Text(busy ? 'Analyzing…' : 'Analyze Evidence')),
              const SizedBox(width: 10),
              OutlinedButton.icon(onPressed: widget.onOpenTests, icon: const Icon(Icons.rule_folder_outlined), label: const Text('View Test Plan')),
            ]),
          ]))),
          const SizedBox(width: 16),
          SizedBox(width: 320, child: Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Session state', style: TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 12),
            _StatePill(widget.session!.state),
            const SizedBox(height: 20),
            const Text('DTCs', style: TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            if (dtcs.isEmpty) const Text('No DTCs recorded yet.', style: TextStyle(color: Colors.white60)),
            for (final dtc in dtcs) ...[
              ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                title: Text(dtc['code']?.toString() ?? '—'),
                subtitle: Text(dtc['description']?.toString() ?? ''),
                trailing: Wrap(
                  spacing: 2,
                  children: [
                    IconButton(
                      tooltip: 'Edit DTC',
                      onPressed: () => setState(() {
                        editingDtcId = dtc['id']?.toString();
                        editDtcController.text = dtc['code']?.toString() ?? '';
                      }),
                      icon: const Icon(Icons.edit_outlined),
                    ),
                    IconButton(
                      tooltip: 'Delete DTC',
                      onPressed: () {
                        final id = dtc['id']?.toString();
                        if (id != null && id.isNotEmpty) widget.onDeleteDtc(id);
                      },
                      icon: const Icon(Icons.delete_outline),
                    ),
                  ],
                ),
              ),
              if (editingDtcId != null && editingDtcId == dtc['id']?.toString())
                Row(
                  children: [
                    Expanded(child: TextField(controller: editDtcController, decoration: const InputDecoration(labelText: 'Edit DTC code'))),
                    const SizedBox(width: 8),
                    IconButton(
                      tooltip: 'Save DTC',
                      onPressed: () async {
                        final id = editingDtcId;
                        if (id == null || editDtcController.text.trim().isEmpty) return;
                        await widget.onUpdateDtc(id, editDtcController.text.trim(), dtc['description']?.toString(), dtc['source']?.toString());
                        if (mounted) setState(() => editingDtcId = null);
                      },
                      icon: const Icon(Icons.check),
                    ),
                    IconButton(
                      tooltip: 'Cancel edit',
                      onPressed: () => setState(() => editingDtcId = null),
                      icon: const Icon(Icons.close),
                    ),
                  ],
                ),
            ],
          ])))),
        ]),
        const SizedBox(height: 18),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Structured symptoms', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(child: TextField(
                      controller: symptomController,
                      minLines: 1,
                      maxLines: 3,
                      decoration: InputDecoration(labelText: editingSymptomId == null ? 'Add symptom' : 'Edit symptom'),
                    )),
                    const SizedBox(width: 8),
                    FilledButton(
                      onPressed: () async {
                        final value = symptomController.text.trim();
                        if (value.isEmpty) return;
                        final id = editingSymptomId;
                        if (id == null) {
                          await widget.onAddSymptom(value);
                        } else {
                          await widget.onUpdateSymptom(id, value);
                        }
                        if (mounted) setState(() { editingSymptomId = null; symptomController.clear(); });
                      },
                      child: Text(editingSymptomId == null ? 'Add' : 'Save'),
                    ),
                    if (editingSymptomId != null)
                      IconButton(
                        tooltip: 'Cancel edit',
                        onPressed: () => setState(() { editingSymptomId = null; symptomController.clear(); }),
                        icon: const Icon(Icons.close),
                      ),
                  ],
                ),
                if (symptoms.isEmpty)
                  const Padding(padding: EdgeInsets.only(top: 10), child: Text('No structured symptoms recorded yet.', style: TextStyle(color: Colors.white60))),
                for (final symptom in symptoms)
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text(symptom['raw_text']?.toString() ?? ''),
                    trailing: Wrap(
                      spacing: 2,
                      children: [
                        IconButton(
                          tooltip: 'Edit symptom',
                          onPressed: () => setState(() {
                            editingSymptomId = symptom['id']?.toString();
                            symptomController.text = symptom['raw_text']?.toString() ?? '';
                          }),
                          icon: const Icon(Icons.edit_outlined),
                        ),
                        IconButton(
                          tooltip: 'Delete symptom',
                          onPressed: () {
                            final id = symptom['id']?.toString();
                            if (id != null && id.isNotEmpty) widget.onDeleteSymptom(id);
                          },
                          icon: const Icon(Icons.delete_outline),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 18),
        Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(child: _EvidenceCard(evidence: evidence)),
          const SizedBox(width: 16),
          Expanded(child: _HypothesisCard(hypotheses: hypotheses)),
        ]),
      ],
    ]);
  }
}

class LiveDataPage extends StatelessWidget {
  const LiveDataPage({super.key, this.session, required this.acquisitionRunning, required this.telemetry, required this.liveSeries, required this.onToggleAcquisition, required this.onRefresh});
  final DiagnosticSessionModel? session;
  final bool acquisitionRunning;
  final Map<String, dynamic> telemetry;
  final Map<String, List<double>> liveSeries;
  final Future<void> Function() onToggleAcquisition;
  final Future<void> Function({bool silent}) onRefresh;

  @override
  Widget build(BuildContext context) {
    final stats = ((telemetry['stats'] as List?) ?? const []).map((e) => SignalStatModel.fromJson(Map<String, dynamic>.from(e as Map))).toList();
    final samples = (telemetry['sample_count'] as num?)?.toInt() ?? 0;
    final events = (telemetry['event_count'] as num?)?.toInt() ?? ((telemetry['events'] as List?)?.length ?? 0);

    return ListView(padding: const EdgeInsets.all(26), children: [
      _PageTitle(title: 'Live Data', subtitle: 'Real-time acquisition, telemetry analytics and signal anomalies.'),
      const SizedBox(height: 20),
      if (session == null) const _EmptyState(icon: Icons.monitor_heart_outlined, title: 'No active session', subtitle: 'Start a diagnostic session first.') else ...[
        Row(children: [
          FilledButton.icon(onPressed: onToggleAcquisition, icon: Icon(acquisitionRunning ? Icons.stop : Icons.play_arrow), label: Text(acquisitionRunning ? 'Stop Acquisition' : 'Start Simulator Acquisition')),
          const SizedBox(width: 10),
          OutlinedButton.icon(onPressed: () => onRefresh(silent: false), icon: const Icon(Icons.refresh), label: const Text('Refresh')), 
          const Spacer(),
          _StatePill(acquisitionRunning ? 'ACQUISITION RUNNING' : 'ACQUISITION STOPPED'),
        ]),
        const SizedBox(height: 18),
        Wrap(spacing: 14, runSpacing: 14, children: [
          _MetricCard(title: 'Samples', value: '$samples', caption: 'telemetry samples', icon: Icons.dataset_outlined),
          _MetricCard(title: 'Signals', value: '${(telemetry['signal_count'] as num?)?.toInt() ?? stats.length}', caption: 'unique PIDs', icon: Icons.tune_outlined),
          _MetricCard(title: 'Events', value: '$events', caption: 'detected signal events', icon: Icons.warning_amber_outlined),
        ]),
        const SizedBox(height: 18),
        if (stats.isEmpty) const _EmptyState(icon: Icons.timeline_outlined, title: 'No telemetry yet', subtitle: 'Start simulator acquisition to populate engine RPM, coolant temperature, speed and throttle.'),
        for (final stat in stats) _SignalCard(stat: stat, values: liveSeries[stat.pid] ?? const []),
      ],
    ]);
  }
}

class NetworkPage extends StatelessWidget {
  const NetworkPage({super.key, this.session, required this.network, required this.onDemo});
  final DiagnosticSessionModel? session;
  final Map<String, dynamic> network;
  final Future<void> Function() onDemo;

  @override
  Widget build(BuildContext context) {
    final nodes = ((network['ecu_candidates'] as List?) ?? (network['nodes'] as List?) ?? const []);
    final buses = ((network['buses'] as List?) ?? const []);
    return ListView(padding: const EdgeInsets.all(26), children: [
      _PageTitle(title: 'ECU Network', subtitle: 'Passive discovery map with observed/inferred ECU candidates.'),
      const SizedBox(height: 20),
      if (session == null) const _EmptyState(icon: Icons.account_tree_outlined, title: 'No active session', subtitle: 'Start a diagnostic session first.') else ...[
        Row(children: [
          FilledButton.icon(onPressed: onDemo, icon: const Icon(Icons.wifi_tethering), label: const Text('Load Demo CAN Traffic')),
          const SizedBox(width: 12),
          Text('${nodes.length} node(s) • ${buses.length} bus(es)', style: const TextStyle(color: Colors.white60)),
        ]),
        const SizedBox(height: 18),
        if (nodes.isEmpty) const _EmptyState(icon: Icons.hub_outlined, title: 'No network map yet', subtitle: 'Load demo traffic or connect a physical CAN/VCI adapter in the device layer.'),
        ...nodes.map((node) {
          final n = Map<String, dynamic>.from(node as Map);
          return Card(margin: const EdgeInsets.only(bottom: 10), child: ListTile(
            leading: CircleAvatar(child: Icon((n['status']?.toString().contains('CONFIRMED') ?? false) ? Icons.verified : Icons.device_unknown)),
            title: Text('${n['bus'] ?? 'CAN0'} • 0x${((n['request_id'] as num?)?.toInt() ?? (n['arbitration_id'] as num?)?.toInt() ?? 0).toRadixString(16).toUpperCase()}'),
            subtitle: Text('Classification: ${n['classification'] ?? n['status'] ?? 'INFERRED'}  •  ${n['confidence'] ?? ''}  •  ${((n['evidence'] as List?) ?? const []).join('; ')}'),
          ));
        }),
      ],
    ]);
  }
}

class TestsPage extends StatelessWidget {
  const TestsPage({super.key, this.session, required this.decision, required this.onRefresh, required this.onRecordTest});
  final DiagnosticSessionModel? session;
  final Map<String, dynamic> decision;
  final Future<void> Function({bool silent}) onRefresh;
  final Future<void> Function(TestCandidateModel candidate, String result, String notes) onRecordTest;

  Future<void> _showRecordDialog(BuildContext context, TestCandidateModel candidate) async {
    var selectedResult = 'INCOMPLETE';
    final notesController = TextEditingController();
    try {
      await showDialog<void>(
        context: context,
        builder: (dialogContext) => StatefulBuilder(
          builder: (context, setDialogState) => AlertDialog(
            title: Text(candidate.name),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Test result'),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  value: selectedResult,
                  items: const [
                    DropdownMenuItem(value: 'PASS', child: Text('PASS')),
                    DropdownMenuItem(value: 'FAIL', child: Text('FAIL')),
                    DropdownMenuItem(value: 'INCOMPLETE', child: Text('INCOMPLETE')),
                  ],
                  onChanged: (value) {
                    if (value != null) setDialogState(() => selectedResult = value);
                  },
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: notesController,
                  minLines: 2,
                  maxLines: 5,
                  decoration: const InputDecoration(labelText: 'Measurements / notes'),
                ),
              ],
            ),
            actions: [
              TextButton(onPressed: () => Navigator.of(dialogContext).pop(), child: const Text('Cancel')),
              FilledButton(
                onPressed: () {
                  final notes = notesController.text.trim();
                  Navigator.of(dialogContext).pop();
                  onRecordTest(candidate, selectedResult, notes);
                },
                child: const Text('Record result'),
              ),
            ],
          ),
        ),
      );
    } finally {
      notesController.dispose();
    }
  }

  @override
  Widget build(BuildContext context) {
    final candidates = ((decision['candidates'] as List?) ?? const []).map((e) => TestCandidateModel.fromJson(Map<String, dynamic>.from(e as Map))).toList();
    return ListView(padding: const EdgeInsets.all(26), children: [
      _PageTitle(title: 'Recommended Tests', subtitle: 'Decision engine balances information gain, evidence fit, cost and risk.'),
      const SizedBox(height: 20),
      if (session == null) const _EmptyState(icon: Icons.rule_folder_outlined, title: 'No active session', subtitle: 'Start a diagnostic session first.') else ...[
        Row(children: [
          FilledButton.tonalIcon(onPressed: () => onRefresh(silent: false), icon: const Icon(Icons.refresh), label: const Text('Refresh Test Plan')),
          const SizedBox(width: 12),
          if (decision['selected_test_id'] != null) Text('Selected by engine: ${decision['selected_test_id'].toString().substring(0, 8)}', style: const TextStyle(color: Colors.white60)),
        ]),
        const SizedBox(height: 18),
        if (candidates.isEmpty) const _EmptyState(icon: Icons.checklist_outlined, title: 'No candidate tests', subtitle: 'Run diagnostic analysis to generate test recommendations.'),
        ...candidates.asMap().entries.map((entry) {
          final index = entry.key + 1;
          final candidate = entry.value;
          return Card(margin: const EdgeInsets.only(bottom: 12), child: Padding(padding: const EdgeInsets.all(18), child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            CircleAvatar(radius: 17, child: Text('$index')),
            const SizedBox(width: 14),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(candidate.name, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
              const SizedBox(height: 5),
              Text(candidate.purpose),
              const SizedBox(height: 10),
              Wrap(spacing: 8, runSpacing: 8, children: [
                _ScoreChip(label: 'Priority ${(candidate.priority * 100).round()}%'),
                _ScoreChip(label: 'Risk ${candidate.risk}'),
                for (final r in candidate.rationale.take(2)) _ScoreChip(label: r),
              ]),
              const SizedBox(height: 10),
              OutlinedButton.icon(
                onPressed: () => _showRecordDialog(context, candidate),
                icon: const Icon(Icons.fact_check_outlined),
                label: const Text('Record result'),
              ),
            ])),
          ])));
        }),
      ],
    ]);
  }
}

class ReportsPage extends StatelessWidget {
  const ReportsPage({super.key, this.session, required this.sessionJson, required this.telemetry});
  final DiagnosticSessionModel? session;
  final Map<String, dynamic> sessionJson;
  final Map<String, dynamic> telemetry;

  @override
  Widget build(BuildContext context) {
    final evidence = ((sessionJson['evidence'] as List?) ?? const []).length;
    final hypotheses = ((sessionJson['hypotheses'] as List?) ?? const []).length;
    final tests = ((sessionJson['test_results'] as List?) ?? const []).length;
    return ListView(padding: const EdgeInsets.all(26), children: [
      _PageTitle(title: 'Reports', subtitle: 'Diagnostic session snapshot and evidence audit trail.'),
      const SizedBox(height: 20),
      if (session == null) const _EmptyState(icon: Icons.description_outlined, title: 'Nothing to report yet', subtitle: 'Complete a diagnostic session first.') else ...[
        Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('${session!.vehicle?.make ?? ''} ${session!.vehicle?.model ?? ''}', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
          const SizedBox(height: 5),
          Text('Session ${session!.id}', style: const TextStyle(color: Colors.white60)),
          const SizedBox(height: 18),
          Wrap(spacing: 14, runSpacing: 14, children: [
            _MetricCard(title: 'Evidence', value: '$evidence', caption: 'provenance records', icon: Icons.fact_check_outlined),
            _MetricCard(title: 'Hypotheses', value: '$hypotheses', caption: 'diagnostic categories', icon: Icons.psychology_outlined),
            _MetricCard(title: 'Tests', value: '$tests', caption: 'recorded results', icon: Icons.checklist_outlined),
            _MetricCard(title: 'Telemetry', value: '${telemetry['sample_count'] ?? 0}', caption: 'samples', icon: Icons.monitor_heart_outlined),
          ]),
        ])),
        const SizedBox(height: 18),
        Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Audit Log', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const SizedBox(height: 12),
          ...(((sessionJson['audit_log'] as List?) ?? const []).reversed.take(15).map((e) => Padding(padding: const EdgeInsets.symmetric(vertical: 5), child: Text(e.toString())))),
        ])),
      ],
    ]);
  }
}

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key, required this.online, required this.apiUrl});
  final bool online;
  final String apiUrl;
  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(26), children: [
    _PageTitle(title: 'Settings', subtitle: 'Desktop workstation runtime and integration settings.'),
    const SizedBox(height: 20),
    Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      _SettingRow(title: 'Backend API', value: apiUrl, icon: Icons.api_outlined),
      _SettingRow(title: 'Connection', value: online ? 'Online' : 'Offline / Demo mode', icon: online ? Icons.cloud_done : Icons.cloud_off),
      const _SettingRow(title: 'AI inference', value: 'Local provider supported; configured in backend', icon: Icons.auto_awesome),
      const _SettingRow(title: 'Safety', value: 'Read-only vehicle diagnostics in MVP/Phase 21', icon: Icons.shield_outlined),
    ]))),
    const SizedBox(height: 16),
    const Card(child: Padding(padding: EdgeInsets.all(20), child: Text('Production deployment: use an authenticated backend, secure device pairing, encrypted local sensitive data, and explicit authorization before any future ECU write/programming capability is introduced.'))),
  ]);
}

class _PageTitle extends StatelessWidget {
  const _PageTitle({required this.title, required this.subtitle});
  final String title;
  final String subtitle;
  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Text(title, style: Theme.of(context).textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800)),
    const SizedBox(height: 6),
    Text(subtitle, style: Theme.of(context).textTheme.bodyLarge?.copyWith(color: Colors.white60)),
  ]);
}

class _MetricCard extends StatelessWidget {
  const _MetricCard({required this.title, required this.value, required this.caption, required this.icon});
  final String title;
  final String value;
  final String caption;
  final IconData icon;
  @override
  Widget build(BuildContext context) => SizedBox(width: 270, child: Card(child: Padding(padding: const EdgeInsets.all(18), child: Row(children: [
    Container(width: 46, height: 46, decoration: BoxDecoration(color: Theme.of(context).colorScheme.primary.withOpacity(.12), borderRadius: BorderRadius.circular(12)), child: Icon(icon, color: Theme.of(context).colorScheme.primary)),
    const SizedBox(width: 13),
    Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(color: Colors.white60)), const SizedBox(height: 3), Text(value, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 17)), Text(caption, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.white54, fontSize: 12))]),
  ])));
}

class _ActionCard extends StatelessWidget {
  const _ActionCard({required this.title, required this.description, required this.action});
  final String title;
  final String description;
  final Widget action;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(22), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18)), const SizedBox(height: 8), Text(description, style: const TextStyle(color: Colors.white70, height: 1.35)), const SizedBox(height: 18), action]));
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.icon, required this.title, required this.subtitle});
  final IconData icon;
  final String title;
  final String subtitle;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(42), child: Column(children: [Icon(icon, size: 42, color: Colors.white38), const SizedBox(height: 12), Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 18)), const SizedBox(height: 6), Text(subtitle, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white60))]));
}

class _EvidenceCard extends StatelessWidget {
  const _EvidenceCard({required this.evidence});
  final List<EvidenceModel> evidence;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    const Text('Evidence', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
    const SizedBox(height: 12),
    if (evidence.isEmpty) const Text('No evidence extracted yet.', style: TextStyle(color: Colors.white60)),
    for (final item in evidence.reversed.take(8)) ListTile(contentPadding: EdgeInsets.zero, dense: true, leading: const Icon(Icons.fact_check_outlined, size: 19), title: Text(item.fact), subtitle: Text('${item.source} • ${item.status}${item.confidence == null ? '' : ' • ${(item.confidence! * 100).round()}%'}')),
  ])));
}

class _HypothesisCard extends StatelessWidget {
  const _HypothesisCard({required this.hypotheses});
  final List<HypothesisModel> hypotheses;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    const Text('Hypotheses', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
    const SizedBox(height: 12),
    if (hypotheses.isEmpty) const Text('Run analysis to generate hypotheses.', style: TextStyle(color: Colors.white60)),
    for (final item in hypotheses.take(8)) ListTile(contentPadding: EdgeInsets.zero, dense: true, leading: _statusIcon(item.status), title: Text(item.statement), subtitle: Text('${item.category} • ${item.status}')),
  ])));

  Widget _statusIcon(String status) => Icon(status.contains('supported') ? Icons.trending_up : status.contains('rejected') ? Icons.remove_circle_outline : Icons.help_outline);
}

class _StatePill extends StatelessWidget {
  const _StatePill(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7), decoration: BoxDecoration(color: Colors.white.withOpacity(.06), borderRadius: BorderRadius.circular(30)), child: Text(text, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)));
}

class _ScoreChip extends StatelessWidget {
  const _ScoreChip({required this.label});
  final String label;
  @override
  Widget build(BuildContext context) => Chip(label: Text(label, style: const TextStyle(fontSize: 11)), visualDensity: VisualDensity.compact);
}

class _SignalCard extends StatelessWidget {
  const _SignalCard({required this.stat, required this.values});
  final SignalStatModel stat;
  final List<double> values;
  @override
  Widget build(BuildContext context) {
    final points = values.length >= 2 ? values : List<double>.generate(2, (_) => stat.mean ?? 0);
    return Card(margin: const EdgeInsets.only(bottom: 10), child: Padding(padding: const EdgeInsets.all(16), child: Row(children: [
      SizedBox(width: 170, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(stat.pid, style: const TextStyle(fontWeight: FontWeight.w800)), Text('${stat.count} samples${stat.unit == null ? '' : ' • ${stat.unit}'}', style: const TextStyle(color: Colors.white54))]),
      SizedBox(width: 300, height: 68, child: CustomPaint(painter: SparklinePainter(points))),
      const Spacer(),
      _SignalValue(label: 'MIN', value: _fmt(stat.min)),
      _SignalValue(label: 'MEAN', value: _fmt(stat.mean)),
      _SignalValue(label: 'MAX', value: _fmt(stat.max)),
      _SignalValue(label: 'ANOM', value: '${stat.anomalyCount}'),
    ])));
  }

  String _fmt(double? value) => value == null ? '—' : value.toStringAsFixed(1);
}

class _SignalValue extends StatelessWidget {
  const _SignalValue({required this.label, required this.value});
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Padding(padding: const EdgeInsets.symmetric(horizontal: 9), child: Column(crossAxisAlignment: CrossAxisAlignment.end, children: [Text(label, style: const TextStyle(fontSize: 10, color: Colors.white38)), const SizedBox(height: 3), Text(value, style: const TextStyle(fontWeight: FontWeight.w700))]));
}

class SparklinePainter extends CustomPainter {
  SparklinePainter(this.values);
  final List<double> values;
  @override
  void paint(Canvas canvas, Size size) {
    if (values.length < 2) return;
    final paint = Paint()..color = const Color(0xFF5DA9FF)..strokeWidth = 2..style = PaintingStyle.stroke;
    final minV = values.reduce((a, b) => math.min(a, b).toDouble());
    final maxV = values.reduce((a, b) => math.max(a, b).toDouble());
    final range = math.max(maxV - minV, 0.0001);
    final path = Path();
    for (var i = 0; i < values.length; i++) {
      final x = i * size.width / (values.length - 1);
      final y = size.height - ((values[i] - minV) / range) * (size.height - 8) - 4;
      if (i == 0) path.moveTo(x, y); else path.lineTo(x, y);
    }
    canvas.drawPath(path, paint);
  }
  @override
  bool shouldRepaint(covariant SparklinePainter oldDelegate) => oldDelegate.values != values;
}

class _SettingRow extends StatelessWidget {
  const _SettingRow({required this.title, required this.value, required this.icon});
  final String title;
  final String value;
  final IconData icon;
  @override
  Widget build(BuildContext context) => Padding(padding: const EdgeInsets.symmetric(vertical: 12), child: Row(children: [Icon(icon, size: 22), const SizedBox(width: 14), SizedBox(width: 180, child: Text(title, style: const TextStyle(fontWeight: FontWeight.w700))), Expanded(child: Text(value, style: const TextStyle(color: Colors.white70)))]));
}
