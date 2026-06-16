import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/appointment.dart';
import '../../providers/auth_provider.dart';
import '../../services/appointment_service.dart';
import '../../services/websocket_service.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';

/// Nurse home screen displaying appointments, queue status, and quick actions
class NurseHomeScreen extends StatefulWidget {
  const NurseHomeScreen({super.key});

  @override
  State<NurseHomeScreen> createState() => _NurseHomeScreenState();
}

class _NurseHomeScreenState extends State<NurseHomeScreen> {
  final AppointmentService _appointmentService = AppointmentService();
  final WebSocketService _wsService = WebSocketService();
  
  List<Appointment> _todayAppointments = [];
  List<Map<String, dynamic>> _allDoctorsQueueStatus = [];
  bool _isLoading = true;
  String? _error;
  StreamSubscription<Map<String, dynamic>>? _wsSubscription;

  @override
  void initState() {
    super.initState();
    _loadData();
    _setupWebSocket();
  }

  @override
  void dispose() {
    _wsSubscription?.cancel();
    super.dispose();
  }

  /// Load appointments and queue status for all doctors
  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // Load today's appointments
      final appointments = await _appointmentService.getAppointments();
      final now = DateTime.now();
      final today = DateTime(now.year, now.month, now.day);
      final tomorrow = today.add(const Duration(days: 1));
      
      _todayAppointments = appointments
          .where((apt) => 
              !apt.isCancelled && 
              apt.scheduledTime.isAfter(today) && 
              apt.scheduledTime.isBefore(tomorrow))
          .toList()
        ..sort((a, b) => a.scheduledTime.compareTo(b.scheduledTime));

      // Load queue status for all doctors
      // Get unique doctor IDs from appointments
      final doctorIds = _todayAppointments
          .map((apt) => apt.doctorId)
          .toSet()
          .toList();

      _allDoctorsQueueStatus = [];
      for (final doctorId in doctorIds) {
        try {
          final queueStatus = await _appointmentService.getQueueStatus(doctorId);
          _allDoctorsQueueStatus.add({
            'doctor_id': doctorId,
            'doctor_name': queueStatus['doctor_name'] ?? 'Doctor',
            'queue_length': queueStatus['queue_length'] ?? 0,
            'patients': queueStatus['patients'] ?? [],
          });
        } catch (e) {
          // Continue loading other doctors even if one fails
          debugPrint('Error loading queue for doctor $doctorId: $e');
        }
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
    
    if (event == 'queue_update' || event == 'appointment_status') {
      // Reload data to get updated queue and appointments
      _loadData();
    }
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);
    final user = authProvider.currentUser;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Nurse Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await authProvider.logout();
              if (context.mounted) {
                Navigator.of(context).pushReplacementNamed('/login');
              }
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: _buildBody(user?.name ?? 'Nurse'),
      ),
    );
  }

  Widget _buildBody(String userName) {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading dashboard...');
    }

    if (_error != null) {
      return ErrorMessage(
        message: _error!,
        onRetry: _loadData,
      );
    }

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildWelcomeSection(userName),
          const SizedBox(height: 24),
          _buildQuickActions(),
          const SizedBox(height: 24),
          _buildAllDoctorsQueueStatus(),
          const SizedBox(height: 24),
          _buildTodayAppointments(),
        ],
      ),
    );
  }

  Widget _buildWelcomeSection(String userName) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          children: [
            CircleAvatar(
              radius: 30,
              backgroundColor: Theme.of(context).colorScheme.primary,
              child: Text(
                userName.isNotEmpty ? userName[0].toUpperCase() : 'N',
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Welcome back,',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[600],
                    ),
                  ),
                  Text(
                    userName,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
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

  Widget _buildQuickActions() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Quick Actions',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildQuickActionCard(
                icon: Icons.person_add,
                label: 'Walk-in Registration',
                color: Colors.green,
                onTap: () {
                  Navigator.of(context).pushNamed('/nurse/walk-in-registration');
                },
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildQuickActionCard(
                icon: Icons.event,
                label: 'View Appointments',
                color: Colors.blue,
                onTap: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Scroll down to view appointments'),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildQuickActionCard(
                icon: Icons.monitor_heart,
                label: 'Record Vitals',
                color: Colors.red,
                onTap: _showVitalsPatientDialog,
              ),
            ),
            const SizedBox(width: 12),
            const Expanded(child: SizedBox.shrink()),
          ],
        ),
      ],
    );
  }

  /// Shows a dialog asking for the patient ID, then navigates to the
  /// vitals entry form with the supplied ID.
  Future<void> _showVitalsPatientDialog() async {
    final controller = TextEditingController();
    final patientId = await showDialog<int>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Record Vitals'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Enter the patient ID to record vitals for:'),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              keyboardType: TextInputType.number,
              autofocus: true,
              decoration: const InputDecoration(
                labelText: 'Patient ID',
                hintText: 'e.g. 42',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              final id = int.tryParse(controller.text.trim());
              if (id != null && id > 0) {
                Navigator.of(ctx).pop(id);
              } else {
                ScaffoldMessenger.of(ctx).showSnackBar(
                  const SnackBar(
                    content: Text('Please enter a valid patient ID'),
                    backgroundColor: Colors.red,
                  ),
                );
              }
            },
            child: const Text('Continue'),
          ),
        ],
      ),
    );

    if (patientId != null && mounted) {
      Navigator.of(context).pushNamed(
        '/vitals/entry',
        arguments: {'patientId': patientId},
      );
    }
  }

  Widget _buildQuickActionCard({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              Icon(
                icon,
                size: 40,
                color: color,
              ),
              const SizedBox(height: 8),
              Text(
                label,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAllDoctorsQueueStatus() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Queue Status - All Doctors',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        if (_allDoctorsQueueStatus.isEmpty)
          _buildEmptyQueueState()
        else
          ..._allDoctorsQueueStatus.map((doctorQueue) => _buildDoctorQueueCard(doctorQueue)),
      ],
    );
  }

  Widget _buildDoctorQueueCard(Map<String, dynamic> doctorQueue) {
    final doctorName = doctorQueue['doctor_name'] as String? ?? 'Doctor';
    final queueLength = doctorQueue['queue_length'] as int? ?? 0;
    final patients = doctorQueue['patients'] as List? ?? [];

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    'Dr. $doctorName',
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: queueLength > 0 
                        ? Colors.orange.withOpacity(0.1)
                        : Colors.green.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: queueLength > 0 ? Colors.orange : Colors.green,
                    ),
                  ),
                  child: Text(
                    '$queueLength ${queueLength == 1 ? 'patient' : 'patients'}',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: queueLength > 0 ? Colors.orange : Colors.green,
                    ),
                  ),
                ),
              ],
            ),
            if (queueLength > 0) ...[
              const SizedBox(height: 12),
              const Divider(),
              const SizedBox(height: 8),
              ...patients.take(2).map((patient) {
                final patientData = patient as Map<String, dynamic>;
                final position = patientData['queue_position'] as int?;
                final name = patientData['patient_name'] as String? ?? 'Patient';
                final waitTime = patientData['estimated_wait_time'] as int? ?? 0;
                
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: Row(
                    children: [
                      Container(
                        width: 32,
                        height: 32,
                        decoration: BoxDecoration(
                          color: position == 1 
                              ? Colors.green.withOpacity(0.2)
                              : Colors.grey.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Center(
                          child: Text(
                            '$position',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              color: position == 1 ? Colors.green : Colors.grey[700],
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
                              name,
                              style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            Text(
                              'Wait: ~$waitTime min',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey[600],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              }),
              if (patients.length > 2)
                Padding(
                  padding: const EdgeInsets.only(top: 8.0),
                  child: Text(
                    '+${patients.length - 2} more in queue',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[600],
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyQueueState() {
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
              'All queues are clear!',
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

  Widget _buildTodayAppointments() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Today\'s Appointments',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        if (_todayAppointments.isEmpty)
          _buildEmptyAppointmentsState()
        else
          ..._todayAppointments.map((appointment) => _buildAppointmentCard(appointment)),
      ],
    );
  }

  Widget _buildEmptyAppointmentsState() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          children: [
            Icon(
              Icons.event_available,
              size: 64,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 16),
            Text(
              'No appointments today',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAppointmentCard(Appointment appointment) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        appointment.patientName ?? 'Patient',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Dr. ${appointment.doctorName ?? 'Doctor'}',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey[600],
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
                            DateFormatter.formatTime(appointment.scheduledTime),
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey[600],
                            ),
                          ),
                          const SizedBox(width: 12),
                          Icon(
                            appointment.isWalkIn ? Icons.directions_walk : Icons.event,
                            size: 14,
                            color: Colors.grey[600],
                          ),
                          const SizedBox(width: 4),
                          Text(
                            appointment.isWalkIn ? 'Walk-in' : 'Scheduled',
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey[600],
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                _buildStatusChip(appointment.status),
              ],
            ),
            if (appointment.queuePosition != null) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: Colors.blue[50],
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.people,
                      size: 16,
                      color: Colors.blue[700],
                    ),
                    const SizedBox(width: 4),
                    Text(
                      'Queue Position: ${appointment.queuePosition}',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.blue[700],
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildStatusChip(String status) {
    Color color;
    String label;

    switch (status) {
      case 'scheduled':
        color = Colors.blue;
        label = 'Scheduled';
        break;
      case 'checked_in':
        color = Colors.orange;
        label = 'Checked In';
        break;
      case 'in_progress':
        color = Colors.green;
        label = 'In Progress';
        break;
      case 'completed':
        color = Colors.grey;
        label = 'Completed';
        break;
      default:
        color = Colors.grey;
        label = status;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: color,
        ),
      ),
    );
  }
}
