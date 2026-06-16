import 'dart:async';
import 'package:flutter/material.dart';
import '../../services/appointment_service.dart';
import '../../services/websocket_service.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';

/// Queue status screen displaying real-time queue information for a doctor
class QueueStatusScreen extends StatefulWidget {
  final int doctorId;
  final String? doctorName;

  const QueueStatusScreen({
    super.key,
    required this.doctorId,
    this.doctorName,
  });

  @override
  State<QueueStatusScreen> createState() => _QueueStatusScreenState();
}

class _QueueStatusScreenState extends State<QueueStatusScreen> {
  final AppointmentService _appointmentService = AppointmentService();
  final WebSocketService _wsService = WebSocketService();
  
  Map<String, dynamic>? _queueData;
  bool _isLoading = true;
  String? _error;
  StreamSubscription<Map<String, dynamic>>? _wsSubscription;

  @override
  void initState() {
    super.initState();
    _loadQueueStatus();
    _setupWebSocket();
  }

  @override
  void dispose() {
    _wsSubscription?.cancel();
    super.dispose();
  }

  /// Load queue status from API
  Future<void> _loadQueueStatus() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final queueData = await _appointmentService.getQueueStatus(widget.doctorId);
      setState(() {
        _queueData = queueData;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  /// Setup WebSocket listener for real-time queue updates
  void _setupWebSocket() {
    _wsSubscription = _wsService.queueUpdates.listen(_handleQueueUpdate);
  }

  /// Handle WebSocket queue update messages
  void _handleQueueUpdate(Map<String, dynamic> message) {
    final data = message['data'] as Map<String, dynamic>?;
    if (data != null && data['doctor_id'] == widget.doctorId) {
      // Reload queue status when update received for this doctor
      _loadQueueStatus();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.doctorName ?? 'Queue Status'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadQueueStatus,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadQueueStatus,
        child: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading queue status...');
    }

    if (_error != null) {
      return ErrorMessage(
        message: _error!,
        onRetry: _loadQueueStatus,
      );
    }

    if (_queueData == null) {
      return const ErrorMessage(
        message: 'No queue data available',
      );
    }

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildQueueSummary(),
          const SizedBox(height: 24),
          _buildPatientsList(),
        ],
      ),
    );
  }

  Widget _buildQueueSummary() {
    final queueLength = _queueData!['queue_length'] as int? ?? 0;
    final averageDuration = _queueData!['average_consultation_duration'] as int? ?? 15;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.info_outline,
                  color: Theme.of(context).colorScheme.primary,
                  size: 28,
                ),
                const SizedBox(width: 12),
                const Text(
                  'Queue Summary',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _buildSummaryItem(
                    icon: Icons.people,
                    label: 'Patients in Queue',
                    value: '$queueLength',
                    color: Colors.blue,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildSummaryItem(
                    icon: Icons.timer,
                    label: 'Avg. Duration',
                    value: '$averageDuration min',
                    color: Colors.orange,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryItem({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 32),
          const SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey[700],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPatientsList() {
    final patients = _queueData!['patients'] as List<dynamic>? ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Patients in Queue',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primary.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '${patients.length} waiting',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (patients.isEmpty)
          _buildEmptyQueue()
        else
          ...patients.asMap().entries.map((entry) {
            final patient = entry.value as Map<String, dynamic>;
            return _buildPatientCard(patient);
          }),
      ],
    );
  }

  Widget _buildEmptyQueue() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          children: [
            Icon(
              Icons.check_circle_outline,
              size: 64,
              color: Colors.green[400],
            ),
            const SizedBox(height: 16),
            Text(
              'No patients in queue',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'The doctor is available',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[500],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPatientCard(Map<String, dynamic> patient) {
    final queuePosition = patient['queue_position'] as int? ?? 0;
    final patientName = patient['patient_name'] as String? ?? 'Patient';
    final estimatedWaitTime = patient['estimated_wait_time'] as int? ?? 0;
    final status = patient['status'] as String? ?? 'scheduled';
    final scheduledTime = patient['scheduled_time'] as String?;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: _getStatusColor(status).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(24),
                  ),
                  child: Center(
                    child: Text(
                      '#$queuePosition',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: _getStatusColor(status),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        patientName,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      _buildStatusChip(status),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            const Divider(),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: _buildInfoItem(
                    icon: Icons.access_time,
                    label: 'Estimated Wait',
                    value: _formatWaitTime(estimatedWaitTime),
                  ),
                ),
                if (scheduledTime != null)
                  Expanded(
                    child: _buildInfoItem(
                      icon: Icons.schedule,
                      label: 'Scheduled',
                      value: DateFormatter.formatTime(DateTime.parse(scheduledTime)),
                    ),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusChip(String status) {
    Color color = _getStatusColor(status);
    String label = _getStatusLabel(status);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color, width: 1),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w600,
          color: color,
        ),
      ),
    );
  }

  Widget _buildInfoItem({
    required IconData icon,
    required String label,
    required String value,
  }) {
    return Row(
      children: [
        Icon(
          icon,
          size: 16,
          color: Colors.grey[600],
        ),
        const SizedBox(width: 4),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                color: Colors.grey[600],
              ),
            ),
            Text(
              value,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'scheduled':
        return Colors.blue;
      case 'checked_in':
        return Colors.orange;
      case 'in_progress':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  String _getStatusLabel(String status) {
    switch (status) {
      case 'scheduled':
        return 'Scheduled';
      case 'checked_in':
        return 'Checked In';
      case 'in_progress':
        return 'In Progress';
      default:
        return status;
    }
  }

  String _formatWaitTime(int minutes) {
    if (minutes < 60) {
      return '$minutes min';
    } else {
      final hours = minutes ~/ 60;
      final mins = minutes % 60;
      return mins > 0 ? '${hours}h ${mins}m' : '${hours}h';
    }
  }
}
