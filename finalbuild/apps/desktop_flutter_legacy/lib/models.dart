class VehicleModel {
  VehicleModel({required this.make, required this.model, this.year, this.engine, this.fuel = const []});
  final String make;
  final String model;
  final int? year;
  final String? engine;
  final List<String> fuel;

  factory VehicleModel.fromJson(Map<String, dynamic> json) => VehicleModel(
        make: json['make'] as String? ?? 'Unknown',
        model: json['model'] as String? ?? 'Vehicle',
        year: json['year'] as int?,
        engine: json['engine'] as String?,
        fuel: ((json['fuel'] as List?) ?? const []).map((e) => e.toString()).toList(),
      );

  Map<String, dynamic> toJson() => {
        'make': make,
        'model': model,
        'year': year,
        'engine': engine,
        'fuel': fuel,
      };
}

class DiagnosticSessionModel {
  DiagnosticSessionModel({required this.id, this.state = 'CREATED', this.vehicle});
  final String id;
  final String state;
  final VehicleModel? vehicle;

  factory DiagnosticSessionModel.fromJson(Map<String, dynamic> json) => DiagnosticSessionModel(
        id: json['session_id']?.toString() ?? '',
        state: json['state']?.toString() ?? 'CREATED',
        vehicle: json['vehicle'] is Map<String, dynamic>
            ? VehicleModel.fromJson(json['vehicle'] as Map<String, dynamic>)
            : null,
      );
}

class EvidenceModel {
  EvidenceModel({required this.fact, required this.source, required this.status, this.confidence});
  final String fact;
  final String source;
  final String status;
  final double? confidence;

  factory EvidenceModel.fromJson(Map<String, dynamic> json) => EvidenceModel(
        fact: json['fact']?.toString() ?? '',
        source: json['source']?.toString() ?? 'UNKNOWN',
        status: json['status']?.toString() ?? '',
        confidence: (json['confidence'] as num?)?.toDouble(),
      );
}

class HypothesisModel {
  HypothesisModel({required this.category, required this.statement, required this.status});
  final String category;
  final String statement;
  final String status;

  factory HypothesisModel.fromJson(Map<String, dynamic> json) => HypothesisModel(
        category: json['category']?.toString() ?? 'Unknown',
        statement: json['statement']?.toString() ?? '',
        status: json['status']?.toString() ?? 'possible',
      );
}

class TestCandidateModel {
  TestCandidateModel({required this.id, required this.name, required this.purpose, required this.priority, required this.risk, this.rationale = const []});
  final String id;
  final String name;
  final String purpose;
  final double priority;
  final String risk;
  final List<String> rationale;

  factory TestCandidateModel.fromJson(Map<String, dynamic> json) => TestCandidateModel(
        id: json['test_id']?.toString() ?? '',
        name: json['name']?.toString() ?? 'Diagnostic test',
        purpose: json['purpose']?.toString() ?? '',
        priority: (json['priority_score'] as num?)?.toDouble() ?? 0,
        risk: json['risk']?.toString() ?? json['risk_level']?.toString() ?? 'LOW',
        rationale: ((json['rationale'] as List?) ?? const []).map((e) => e.toString()).toList(),
      );
}

class SignalStatModel {
  SignalStatModel({required this.pid, required this.count, this.unit, this.min, this.max, this.mean, this.anomalyCount = 0, this.eventCount = 0});
  final String pid;
  final int count;
  final String? unit;
  final double? min;
  final double? max;
  final double? mean;
  final int anomalyCount;
  final int eventCount;

  factory SignalStatModel.fromJson(Map<String, dynamic> json) => SignalStatModel(
        pid: json['pid']?.toString() ?? '',
        count: (json['count'] as num?)?.toInt() ?? 0,
        unit: json['unit']?.toString(),
        min: (json['min_value'] as num?)?.toDouble(),
        max: (json['max_value'] as num?)?.toDouble(),
        mean: (json['mean'] as num?)?.toDouble(),
        anomalyCount: (json['anomaly_count'] as num?)?.toInt() ?? 0,
        eventCount: (json['event_count'] as num?)?.toInt() ?? 0,
      );
}
