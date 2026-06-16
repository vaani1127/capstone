import 'package:flutter/material.dart';

/// Allergy model representing a patient's allergy record.
class Allergy {
  final int id;
  final int patientId;
  final int recordedBy;
  final String? recordedByName;
  final String allergen;
  final String? reaction;
  final String severity;
  final DateTime? onsetDate;
  final bool isActive;
  final String? notes;
  final DateTime createdAt;
  final DateTime updatedAt;

  Allergy({
    required this.id,
    required this.patientId,
    required this.recordedBy,
    this.recordedByName,
    required this.allergen,
    this.reaction,
    required this.severity,
    this.onsetDate,
    required this.isActive,
    this.notes,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Allergy.fromJson(Map<String, dynamic> json) {
    return Allergy(
      id: json['id'] as int,
      patientId: json['patient_id'] as int,
      recordedBy: json['recorded_by'] as int,
      recordedByName: json['recorded_by_name'] as String?,
      allergen: json['allergen'] as String,
      reaction: json['reaction'] as String?,
      severity: json['severity'] as String,
      onsetDate: json['onset_date'] != null
          ? DateTime.parse(json['onset_date'] as String)
          : null,
      isActive: json['is_active'] as bool,
      notes: json['notes'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      updatedAt: DateTime.parse(json['updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'patient_id': patientId,
      'recorded_by': recordedBy,
      'recorded_by_name': recordedByName,
      'allergen': allergen,
      'reaction': reaction,
      'severity': severity,
      'onset_date': onsetDate != null
          ? '${onsetDate!.year.toString().padLeft(4, '0')}-'
              '${onsetDate!.month.toString().padLeft(2, '0')}-'
              '${onsetDate!.day.toString().padLeft(2, '0')}'
          : null,
      'is_active': isActive,
      'notes': notes,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  /// Background colour for UI cards and chips based on clinical severity.
  ///
  /// severe   = red    (immediate danger)
  /// moderate = orange (significant risk)
  /// mild     = amber  (low risk)
  Color get severityColor {
    switch (severity) {
      case 'severe':
        return Colors.red;
      case 'moderate':
        return Colors.orange;
      case 'mild':
        return Colors.amber;
      default:
        return Colors.grey;
    }
  }

  /// Capitalised severity label for display.
  String get severityLabel =>
      severity.isEmpty ? '' : severity[0].toUpperCase() + severity.substring(1);
}
