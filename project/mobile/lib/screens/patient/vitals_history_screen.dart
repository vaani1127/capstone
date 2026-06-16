import 'package:flutter/material.dart';
import '../../models/vitals.dart';
import '../../services/vitals_service.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';

/// Displays a patient's complete vitals history as a vertical timeline.
///
/// Usage:
///   // Patient viewing own vitals (no patientId needed):
///   Navigator.of(context).pushNamed('/vitals/history');
///
///   // Doctor/Nurse viewing a specific patient:
///   Navigator.of(context).pushNamed('/vitals/history',
///     arguments: {'patientId': id, 'patientName': 'Jane Doe'});
///
/// When [patientId] is null the screen calls GET /vitals/me (patient self-view).
/// When [patientId] is provided it calls GET /vitals/patient/{patientId}.
class VitalsHistoryScreen extends StatefulWidget {
  final int? patientId;
  final String? patientName;

  const VitalsHistoryScreen({super.key, this.patientId, this.patientName});

  @override
  State<VitalsHistoryScreen> createState() => _VitalsHistoryScreenState();
}

class _VitalsHistoryScreenState extends State<VitalsHistoryScreen> {
  final VitalsService _vitalsService = VitalsService();

  List<Vitals> _vitals = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final rows = widget.patientId != null
          ? await _vitalsService.getPatientVitals(widget.patientId!)
          : await _vitalsService.getMyVitals();
      setState(() {
        _vitals = rows;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    final title = widget.patientName != null
        ? '${widget.patientName}\'s Vitals'
        : 'My Vitals';

    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: RefreshIndicator(
        onRefresh: _load,
        child: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading vitals history...');
    }
    if (_error != null) {
      return ErrorMessage(message: _error!, onRetry: _load);
    }
    if (_vitals.isEmpty) {
      return _buildEmpty();
    }
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      itemCount: _vitals.length,
      itemBuilder: (context, i) => _buildTimelineCard(_vitals[i], i),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.monitor_heart_outlined, size: 80, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text(
            'No vitals recorded yet',
            style: TextStyle(fontSize: 18, color: Colors.grey[600]),
          ),
          const SizedBox(height: 8),
          Text(
            'Vitals will appear here once a nurse or doctor records them.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 14, color: Colors.grey[500]),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Timeline card
  // ---------------------------------------------------------------------------

  Widget _buildTimelineCard(Vitals v, int index) {
    final isFirst = index == 0;
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Timeline column
          SizedBox(
            width: 28,
            child: Column(
              children: [
                Container(
                  width: 12,
                  height: 12,
                  margin: const EdgeInsets.only(top: 18),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isFirst
                        ? Theme.of(context).colorScheme.primary
                        : Colors.grey[400],
                  ),
                ),
                Expanded(
                  child: Center(
                    child: Container(width: 2, color: Colors.grey[300]),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          // Card
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Card(
                elevation: isFirst ? 2 : 1,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: isFirst
                      ? BorderSide(
                          color: Theme.of(context).colorScheme.primary
                              .withOpacity(0.3),
                        )
                      : BorderSide.none,
                ),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildCardHeader(v, isFirst),
                      const SizedBox(height: 12),
                      _buildVitalsGrid(v),
                      if (v.notes != null && v.notes!.isNotEmpty) ...[
                        const SizedBox(height: 10),
                        _buildNotes(v.notes!),
                      ],
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCardHeader(Vitals v, bool isLatest) {
    return Row(
      children: [
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                DateFormatter.formatDateTime(v.recordedAt),
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                ),
              ),
              if (v.recordedByName != null)
                Text(
                  'Recorded by ${v.recordedByName}',
                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                ),
            ],
          ),
        ),
        if (isLatest)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.primary.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                  color: Theme.of(context).colorScheme.primary.withOpacity(0.4)),
            ),
            child: Text(
              'Latest',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: Theme.of(context).colorScheme.primary,
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildVitalsGrid(Vitals v) {
    final items = <Widget>[];

    // Blood pressure
    if (v.systolicBp != null || v.diastolicBp != null) {
      final bpText = '${v.systolicBp ?? '--'}/${v.diastolicBp ?? '--'} mmHg';
      items.add(_buildVitalChip(
        icon: Icons.favorite,
        label: 'BP',
        value: bpText,
        isAlert: v.isBpElevated,
      ));
    }

    // Heart rate
    if (v.heartRate != null) {
      items.add(_buildVitalChip(
        icon: Icons.monitor_heart,
        label: 'HR',
        value: '${v.heartRate} bpm',
        isAlert: v.isHeartRateAbnormal,
      ));
    }

    // SpO2
    if (v.oxygenSaturation != null) {
      items.add(_buildVitalChip(
        icon: Icons.air,
        label: 'SpO2',
        value: '${v.oxygenSaturation!.toStringAsFixed(1)}%',
        isAlert: v.isSpO2Low,
      ));
    }

    // Temperature
    if (v.temperature != null) {
      items.add(_buildVitalChip(
        icon: Icons.thermostat,
        label: 'Temp',
        value: '${v.temperature!.toStringAsFixed(1)} °F',
        isAlert: v.isTempElevated,
      ));
    }

    // Respiratory rate
    if (v.respiratoryRate != null) {
      items.add(_buildVitalChip(
        icon: Icons.waves,
        label: 'RR',
        value: '${v.respiratoryRate} br/min',
        isAlert: false,
      ));
    }

    // Weight / Height / BMI
    if (v.weightKg != null) {
      items.add(_buildVitalChip(
        icon: Icons.monitor_weight,
        label: 'Weight',
        value: '${v.weightKg!.toStringAsFixed(1)} kg',
        isAlert: false,
      ));
    }
    if (v.heightCm != null) {
      items.add(_buildVitalChip(
        icon: Icons.height,
        label: 'Height',
        value: '${v.heightCm!.toStringAsFixed(0)} cm',
        isAlert: false,
      ));
    }
    if (v.bmi != null) {
      final bmiAlert = v.bmi! < 18.5 || v.bmi! >= 30;
      items.add(_buildVitalChip(
        icon: Icons.calculate,
        label: 'BMI',
        value: v.bmi!.toStringAsFixed(1),
        isAlert: bmiAlert,
      ));
    }

    if (items.isEmpty) {
      return Text(
        'No measurements recorded',
        style: TextStyle(color: Colors.grey[500], fontSize: 13),
      );
    }

    return Wrap(spacing: 8, runSpacing: 8, children: items);
  }

  Widget _buildVitalChip({
    required IconData icon,
    required String label,
    required String value,
    required bool isAlert,
  }) {
    final color = isAlert ? Colors.red : Colors.grey[700]!;
    final bg = isAlert ? Colors.red.withOpacity(0.08) : Colors.grey[100]!;
    final border =
        isAlert ? Colors.red.withOpacity(0.3) : Colors.grey.withOpacity(0.2);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: border),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: TextStyle(
                  fontSize: 10,
                  color: color.withOpacity(0.7),
                  fontWeight: FontWeight.w500,
                ),
              ),
              Text(
                value,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: color,
                ),
              ),
            ],
          ),
          if (isAlert) ...[
            const SizedBox(width: 4),
            Icon(Icons.warning_amber_rounded, size: 12, color: Colors.red),
          ],
        ],
      ),
    );
  }

  Widget _buildNotes(String notes) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.blue[50],
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.notes, size: 14, color: Colors.blue[600]),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              notes,
              style: TextStyle(fontSize: 13, color: Colors.blue[800]),
            ),
          ),
        ],
      ),
    );
  }
}
