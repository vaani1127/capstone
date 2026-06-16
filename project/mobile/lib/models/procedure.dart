/// Procedure model representing a clinical procedure performed on a patient.
class Procedure {
  final int id;
  final int patientId;
  final int? encounterId;
  final int? performedBy;
  final String? performedByName;
  final String? procedureCode;
  final String description;
  final DateTime performedAt;
  final int? durationMinutes;
  final String? outcome;
  final double? baseCost;
  final String? notes;
  final DateTime createdAt;

  Procedure({
    required this.id,
    required this.patientId,
    this.encounterId,
    this.performedBy,
    this.performedByName,
    this.procedureCode,
    required this.description,
    required this.performedAt,
    this.durationMinutes,
    this.outcome,
    this.baseCost,
    this.notes,
    required this.createdAt,
  });

  factory Procedure.fromJson(Map<String, dynamic> json) {
    return Procedure(
      id: json['id'] as int,
      patientId: json['patient_id'] as int,
      encounterId: json['encounter_id'] as int?,
      performedBy: json['performed_by'] as int?,
      performedByName: json['performed_by_name'] as String?,
      procedureCode: json['procedure_code'] as String?,
      description: json['description'] as String,
      performedAt: DateTime.parse(json['performed_at'] as String),
      durationMinutes: json['duration_minutes'] as int?,
      outcome: json['outcome'] as String?,
      baseCost: (json['base_cost'] as num?)?.toDouble(),
      notes: json['notes'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  /// Formatted cost string, e.g. "$1,250.00".
  String get costLabel {
    if (baseCost == null) return 'N/A';
    return '\$${baseCost!.toStringAsFixed(2).replaceAllMapped(
          RegExp(r'(\d)(?=(\d{3})+\.)'),
          (m) => '${m[1]},',
        )}';
  }
}
