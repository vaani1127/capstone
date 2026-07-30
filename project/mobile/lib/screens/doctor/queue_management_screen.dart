import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/appointment.dart';
import '../../providers/auth_provider.dart';
import '../../services/appointment_service.dart';
import '../../services/api_client.dart';
import '../../services/websocket_service.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';

/// Queue management screen for doctors to manage patient queue
class QueueManagementScreen extends StatefulWidget {
  const QueueManagementScreen({super.key});

  @override
  State<QueueManagementScreen> createState() => _QueueManagementScreenState();
}

class _QueueManagementScreenState extends State<QueueManagementScreen> {
  final AppointmentService _appointmentService = AppointmentService();
  final ApiClient _apiClient = ApiClient();
  final WebSocketService _wsService = WebSocketService();
  
  List<Map<String, dynamic>> _queuePatients = [];
  bool _isLoading = true;
  String? _error;
  StreamSubscription<Map<String, dynamic>>? _wsSubscription;
  int? _doctorId;
  bool _isUpdating = false;

  @override
  void initState() {
    super.initState();
    _initializeScreen();
  }

  @override
  void dispose() {
    _wsSubscription?.cancel();
    super.dispose();
  }

  /// Initialize screen by loading doctor data
  Future<void> _initializeScreen() async {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    final user = authProvider.currentUser;
    
    if (user != null && user.isDoctor) {
      // Get doctor ID from user ID
      _doctorId = user.id;
      await _loadQueueData();
      _setupWebSocket();
    }
  }

  /// Load queue data from API
  Future<void> _loadQueueData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      if (_doctorId != null) {
        final queueStatus = await _appointmentService.getQueueStatus(_doctorId!);
        final patients = queueStatus['patients'] as List? ?? [];
        
        _queuePatients = patients.map((p) => p as Map<String, dynamic>).toList();
        
        // Sort by queue position
        _queuePatients.sort((a, b) {
          final posA = a['queue_position'] as int? ?? 999;
          final posB = b['queue_position'] as int? ?? 999;
          return posA.compareTo(posB);
        });
      }

      setState(() {
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  /// Setup WebSocket listener for real-time updates
  void _setupWebSocket() {
    _wsSubscription = _wsService.messages.listen(_handleWebSocketMessage);
  }

  /// Handle WebSocket messages
  void _handleWebSocketMessage(Map<String, dynamic> message) {
    final event = message['event'] as String?;
    
    if (event == 'queue_update') {
      final data = message['data'] as Map<String, dynamic>;
      final doctorId = data['doctor_id'] as int?;
      
      if (doctorId == _doctorId) {
        // Reload queue data
        _loadQueueData();
      }
    } else if (event == 'appointment_status') {
      // Reload queue data on status changes
      _loadQueueData();
    }
  }

  /// Update appointment status
  Future<void> _updateAppointmentStatus(int appointmentId, String newStatus) async {
    if (_isUpdating) return;

    setState(() {
      _isUpdating = true;
    });

    try {
      await _apiClient.patch('/appointments/$appointmentId/status', {
        'status': newStatus,
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Appointment status updated to $newStatus'),
            backgroundColor: Colors.green,
          ),
        );
      }

      // Reload queue data
      await _loadQueueData();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to update status: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      setState(() {
        _isUpdating = false;
      });
    }
  }

  /// Start consultation by navigating to consultation screen
  Future<void> _startConsultation(Map<String, dynamic> patient) async {
    final appointmentId = patient['appointment_id'] as int?;
    final patientId = patient['patient_id'] as int?;
    final patientName = patient['patient_name'] as String? ?? 'Patient';
    final status = patient['status'] as String? ?? 'scheduled';
    final scheduledTime = patient['scheduled_time'] as String?;
    final appointmentType = patient['appointment_type'] as String? ?? 'scheduled';

    if (appointmentId == null || patientId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Invalid appointment data'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    // Create appointment object
    final appointment = Appointment(
      id: appointmentId,
      patientId: patientId,
      doctorId: _doctorId!,
      scheduledTime: scheduledTime != null 
          ? DateTime.parse(scheduledTime) 
          : DateTime.now(),
      status: status,
      appointmentType: appointmentType,
      queuePosition: patient['queue_position'] as int?,
      patientName: patientName,
      doctorName: null,
      createdAt: DateTime.now(),
    );

    // Update status to in_progress first
    await _updateAppointmentStatus(appointmentId, 'in_progress');

    // Navigate to consultation screen
    if (mounted) {
      Navigator.of(context).pushNamed(
        '/doctor/consultation',
        arguments: {'appointment': appointment},
      );
    }
  }

  /// Show confirmation dialog before updating status
  Future<void> _confirmStatusUpdate(int appointmentId, String patientName, String newStatus) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirm Status Update'),
        content: Text(
          'Mark consultation with $patientName as ${newStatus.replaceAll('_', ' ')}?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: ElevatedButton.styleFrom(
              backgroundColor: newStatus == 'in_progress'
                  ? Colors.green
                  : newStatus == 'no_show'
                      ? Colors.red
                      : Colors.blue,
              foregroundColor: Colors.white,
            ),
            child: const Text('Confirm'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await _updateAppointmentStatus(appointmentId, newStatus);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Queue Management'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _isLoading ? null : _loadQueueData,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadQueueData,
        child: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading queue...');
    }

    if (_error != null) {
      return ErrorMessage(
        message: _error!,
        onRetry: _loadQueueData,
      );
    }

    if (_queuePatients.isEmpty) {
      return _buildEmptyQueueState();
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16.0),
      itemCount: _queuePatients.length + 1,
      itemBuilder: (context, index) {
        if (index == 0) {
          return _buildQueueHeader();
        }
        return _buildQueuePatientCard(_queuePatients[index - 1]);
      },
    );
  }

  Widget _buildQueueHeader() {
    return Card(
      color: Theme.of(context).colorScheme.primaryContainer,
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          children: [
            Icon(
              Icons.people,
              size: 32,
              color: Theme.of(context).colorScheme.onPrimaryContainer,
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Patients in Queue',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Theme.of(context).colorScheme.onPrimaryContainer,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${_queuePatients.length} ${_queuePatients.length == 1 ? 'patient' : 'patients'} waiting',
                    style: TextStyle(
                      fontSize: 14,
                      color: Theme.of(context).colorScheme.onPrimaryContainer.withOpacity(0.8),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyQueueState() {
    return Center(
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.check_circle_outline,
                size: 80,
                color: Colors.green[400],
              ),
              const SizedBox(height: 24),
              const Text(
                'No patients in queue',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'You\'re all caught up!',
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.grey[600],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildQueuePatientCard(Map<String, dynamic> patient) {
    final appointmentId = patient['appointment_id'] as int?;
    final queuePosition = patient['queue_position'] as int?;
    final patientName = patient['patient_name'] as String? ?? 'Patient';
    final status = patient['status'] as String? ?? 'scheduled';
    final waitTime = patient['estimated_wait_time'] as int? ?? 0;
    final appointmentType = patient['appointment_type'] as String? ?? 'scheduled';
    final scheduledTime = patient['scheduled_time'] as String?;

    if (appointmentId == null || queuePosition == null) {
      return const SizedBox.shrink();
    }

    final isFirst = queuePosition == 1;
    final isInProgress = status == 'in_progress';
    final isCheckedIn = status == 'checked_in';
    // Backend only allows the SCHEDULED -> NO_SHOW transition
    // (see AppointmentStatus enum / update_appointment_status endpoint),
    // so the "Mark No-Show" action is only offered while still scheduled.
    final isScheduled = status == 'scheduled';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: isFirst ? 4 : 1,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                // Queue position badge
                Container(
                  width: 50,
                  height: 50,
                  decoration: BoxDecoration(
                    color: isFirst 
                        ? Colors.green.withOpacity(0.2)
                        : Colors.grey.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: isFirst ? Colors.green : Colors.grey,
                      width: 2,
                    ),
                  ),
                  child: Center(
                    child: Text(
                      '$queuePosition',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: isFirst ? Colors.green : Colors.grey[700],
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                // Patient info
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        patientName,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Icon(
                            Icons.access_time,
                            size: 14,
                            color: Colors.grey[600],
                          ),
                          const SizedBox(width: 4),
                          Text(
                            'Wait: ~$waitTime min',
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.grey[600],
                            ),
                          ),
                          const SizedBox(width: 12),
                          Icon(
                            appointmentType == 'walk_in' 
                                ? Icons.directions_walk 
                                : Icons.event,
                            size: 14,
                            color: Colors.grey[600],
                          ),
                          const SizedBox(width: 4),
                          Text(
                            appointmentType == 'walk_in' ? 'Walk-in' : 'Scheduled',
                            style: TextStyle(
                              fontSize: 13,
                              color: Colors.grey[600],
                            ),
                          ),
                        ],
                      ),
                      if (scheduledTime != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          'Scheduled: ${DateFormatter.formatTime(DateTime.parse(scheduledTime))}',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[500],
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                // Status badge
                _buildStatusChip(status),
              ],
            ),
            const SizedBox(height: 16),
            // Action buttons
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                if (!isInProgress && (isFirst || isCheckedIn))
                  ElevatedButton.icon(
                    onPressed: _isUpdating 
                        ? null 
                        : () => _startConsultation(patient),
                    icon: const Icon(Icons.play_arrow),
                    label: const Text('Start'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                    ),
                  ),
                if (isInProgress) ...[
                  const SizedBox(width: 8),
                  ElevatedButton.icon(
                    onPressed: _isUpdating 
                        ? null 
                        : () => _confirmStatusUpdate(appointmentId, patientName, 'completed'),
                    icon: const Icon(Icons.check),
                    label: const Text('Complete'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blue,
                      foregroundColor: Colors.white,
                    ),
                  ),
                ],
                if (isScheduled) ...[
                  const SizedBox(width: 8),
                  OutlinedButton.icon(
                    onPressed: _isUpdating
                        ? null
                        : () => _confirmStatusUpdate(appointmentId, patientName, 'no_show'),
                    icon: const Icon(Icons.person_off, size: 18),
                    label: const Text('Mark No-Show'),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.red[700],
                      side: BorderSide(color: Colors.red[300]!),
                    ),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusChip(String status) {
    Color color;
    String label;
    IconData icon;

    switch (status) {
      case 'scheduled':
        color = Colors.blue;
        label = 'Scheduled';
        icon = Icons.schedule;
        break;
      case 'checked_in':
        color = Colors.orange;
        label = 'Checked In';
        icon = Icons.how_to_reg;
        break;
      case 'in_progress':
        color = Colors.green;
        label = 'In Progress';
        icon = Icons.medical_services;
        break;
      case 'completed':
        color = Colors.grey;
        label = 'Completed';
        icon = Icons.check_circle;
        break;
      case 'no_show':
        color = Colors.red;
        label = 'No-Show';
        icon = Icons.person_off;
        break;
      default:
        color = Colors.grey;
        label = status;
        icon = Icons.info;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: 14,
            color: color,
          ),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}
