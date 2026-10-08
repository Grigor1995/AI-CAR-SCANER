import 'package:dio/dio.dart';

class DiagnosticApiClient {
  DiagnosticApiClient({String? baseUrl})
      : _dio = Dio(BaseOptions(
          baseUrl: baseUrl ?? const String.fromEnvironment('API_URL', defaultValue: 'http://127.0.0.1:8000'),
          connectTimeout: const Duration(seconds: 2),
          receiveTimeout: const Duration(seconds: 8),
          sendTimeout: const Duration(seconds: 8),
          headers: {'Content-Type': 'application/json'},
        ));

  final Dio _dio;


  Future<List<String>> catalogMakes() async {
    final response = await _dio.get('/api/v1/vehicle-catalog/makes');
    return ((response.data as List?) ?? const []).map((e) => e.toString()).toList();
  }

  Future<List<String>> catalogModels(String make) async {
    final response = await _dio.get('/api/v1/vehicle-catalog/models', queryParameters: {'make': make});
    return ((response.data as List?) ?? const []).map((e) => e.toString()).toList();
  }

  Future<List<String>> catalogChassis(String make, String model) async {
    final response = await _dio.get('/api/v1/vehicle-catalog/chassis', queryParameters: {'make': make, 'model': model});
    return ((response.data as List?) ?? const []).map((e) => e.toString()).toList();
  }

  Future<List<int>> catalogYears(String make, String model, {String? chassis}) async {
    final response = await _dio.get('/api/v1/vehicle-catalog/years', queryParameters: {
      'make': make,
      'model': model,
      if (chassis != null && chassis.isNotEmpty) 'chassis': chassis,
    });
    return ((response.data as List?) ?? const []).map((e) => (e as num).toInt()).toList();
  }

  Future<List<String>> catalogEngines(String make, String model, {int? year, String? chassis}) async {
    final response = await _dio.get('/api/v1/vehicle-catalog/engines', queryParameters: {
      'make': make,
      'model': model,
      if (year != null) 'year': year,
      if (chassis != null && chassis.isNotEmpty) 'chassis': chassis,
    });
    return ((response.data as List?) ?? const []).map((e) => e.toString()).toList();
  }

  Future<List<String>> catalogEcus(String make, String model, String engine, {int? year, String? chassis}) async {
    final response = await _dio.get('/api/v1/vehicle-catalog/ecus', queryParameters: {
      'make': make,
      'model': model,
      'engine': engine,
      if (year != null) 'year': year,
      if (chassis != null && chassis.isNotEmpty) 'chassis': chassis,
    });
    return ((response.data as List?) ?? const []).map((e) => e.toString()).toList();
  }

  Future<bool> health() async {
    try {
      final response = await _dio.get('/health');
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<List<Map<String, dynamic>>> listSessions({int limit = 50}) async {
    final response = await _dio.get('/api/v1/sessions', queryParameters: {'limit': limit});
    return ((response.data as List?) ?? const [])
        .map((item) => Map<String, dynamic>.from(item as Map))
        .toList();
  }

  Future<Map<String, dynamic>> createSession({Map<String, dynamic>? vehicle}) async {
    final response = await _dio.post('/api/v1/sessions', data: vehicle);
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> addDtc(String id, String code, {String? description}) async {
    final response = await _dio.post('/api/v1/sessions/$id/dtcs', data: {
      'code': code,
      'description': description,
      'source': 'USER_REPORTED',
    });
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<List<Map<String, dynamic>>> acquisitionRecords(String id, {int limit = 200}) async {
    final response = await _dio.get('/api/v1/acquisition/sessions/$id/records', queryParameters: {'limit': limit});
    final data = Map<String, dynamic>.from(response.data as Map);
    return ((data['records'] as List?) ?? const []).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  Future<Map<String, dynamic>> getSession(String id) async {
    final response = await _dio.get('/api/v1/sessions/$id');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> ingestEvidence(String id, String text) async {
    final response = await _dio.post('/api/v1/intelligence/sessions/$id/evidence/text', data: {'text': text});
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> analyze(String id, {String language = 'en'}) async {
    final response = await _dio.post(
      '/api/v1/analysis/$id',
      queryParameters: {'language': language},
    );
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> decisionPlan(String id) async {
    final response = await _dio.get('/api/v1/decision/sessions/$id/plan');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> telemetrySummary(String id) async {
    final response = await _dio.get('/api/v1/telemetry/sessions/$id/summary');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> startSimulator(String id) async {
    final response = await _dio.post('/api/v1/acquisition/sessions/$id/start', data: {'adapter': 'simulator'});
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> stopAcquisition(String id) async {
    final response = await _dio.post('/api/v1/acquisition/sessions/$id/stop');
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> networkDiscovery(String id) async {
    final response = await _dio.get('/api/v1/network-discovery/sessions/$id/map');
    return Map<String, dynamic>.from(response.data as Map);
  }
  Future<Map<String, dynamic>> ingestCanFrames(String id, String bus, List<Map<String, dynamic>> frames) async {
    final response = await _dio.post('/api/v1/network-discovery/sessions/$id/frames', data: {'bus': bus, 'frames': frames});
    return Map<String, dynamic>.from(response.data as Map);
  }
}
