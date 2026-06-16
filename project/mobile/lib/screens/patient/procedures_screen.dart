import 'package:flutter/material.dart';
import '../../models/procedure.dart';
import '../../services/procedure_service.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';

/// Displays a patient's procedure history as a vertical timeline.
///
/// When [patientId] is null the screen calls GET /procedures/me (patient's
/// own view).  When [patientId] is provided it calls
/// GET /procedures/patient/{patientId} (doctor/admin view of a specific patient).
class ProceduresScreen extends StatefulWidget {
  final int? patientId;
  final String? patientName;

  const ProceduresScreen({super.key, this.patientId, this.patientName});

  @override
  State<ProceduresScreen> createState() => _ProceduresScreenState();
}

class _ProceduresScreenState extends State<ProceduresScreen> {
  final ProcedureService _service = ProcedureService();

  List<Procedure> _procedures = [];
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
          ? await _service.getPatientProcedures(widget.patientId!)
          : await _service.getMyProcedures();
      setState(() {
        _procedures = rows;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final title = widget.patientName != null
        ? '${widget.patientName}\'s Procedures'
        : 'My Procedures';
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: RefreshIndicator(onRefresh: _load, child: _buildBody()),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading procedure history...');
    }
    if (_error != null) {
      return ErrorMessage(message: _error!, onRetry: _load);
    }
    if (_procedures.isEmpty) {
      return _buildEmpty();
    }
    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      itemCount: _procedures.length,
      itemBuilder: (_, i) => _buildTimelineCard(_procedures[i], i),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.medical_services_outlined, size: 80, color: Colors.grey[400]),
          const SizedBox(height: 16),
          const Text(
            'No procedures recorded.',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          Text(
            'Procedures performed by your care team will appear here.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 14, color: Colors.grey[600]),
          ),
        ],
      ),
    );
  }

  Widget _buildTimelineCard(Procedure proc, int index) {
    final isFirst = index == 0;
    final primary = Theme.of(context).colorScheme.primary;

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Timeline rail
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
                    color: isFirst ? primary : Colors.grey[400],
                  ),
                ),
                Expanded(
                  child: Center(child: Container(width: 2, color: Colors.grey[300])),
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
                      ? BorderSide(color: primary.withOpacity(0.3))
                      : BorderSide.none,
                ),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Description
                      Text(
                        proc.description,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      if (proc.procedureCode != null) ...[
                        const SizedBox(height: 2),
                        Text(
                          'Code: ${proc.procedureCode}',
                          style: TextStyle(fontSize: 12, color: Colors.grey[500]),
                        ),
                      ],
                      const SizedBox(height: 8),
                      // Meta chips
                      Wrap(
                        spacing: 8,
                        runSpacing: 4,
                        children: [
                          _chip(
                            Icons.calendar_today,
                            DateFormatter.formatDateTime(proc.performedAt),
                            Colors.blue,
                          ),
                          if (proc.performedByName != null)
                            _chip(Icons.person, proc.performedByName!, Colors.teal),
                          if (proc.durationMinutes != null)
                            _chip(Icons.timer, '${proc.durationMinutes} min',
                                Colors.orange),
                          _chip(Icons.attach_money, proc.costLabel, Colors.green),
                        ],
                      ),
                      // Outcome
                      if (proc.outcome != null && proc.outcome!.isNotEmpty) ...[
                        const SizedBox(height: 8),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: Colors.green.shade50,
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Icon(Icons.check_circle_outline,
                                  size: 14, color: Colors.green[700]),
                              const SizedBox(width: 6),
                              Expanded(
                                child: Text(
                                  proc.outcome!,
                                  style: TextStyle(
                                      fontSize: 13, color: Colors.green[800]),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                      // Notes
                      if (proc.notes != null && proc.notes!.isNotEmpty) ...[
                        const SizedBox(height: 6),
                        Text(
                          proc.notes!,
                          style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey[600],
                              fontStyle: FontStyle.italic),
                        ),
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

  Widget _chip(IconData icon, String label, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.25)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: color.withOpacity(0.8)),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
                fontSize: 12, color: color.withOpacity(0.9), fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }
}
