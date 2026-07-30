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
import 'patient_search_screen.dart';

/// Doctor home screen displaying appointments, queue, and quick actions
class DoctorHomeScreen extends StatefulWidget {
  const DoctorHomeScreen({super.key});

  @override
  State<DoctorHomeScreen> createState() => _DoctorHomeScreenState();
}

class _DoctorHomeScreenState extends State<DoctorHomeScreen> {
  final AppointmentService _appointmentService = AppointmentService();
  final WebSocketService _wsService = WebSocketService();
  
  List<Appointment> _todayAppointments = [];
  Map<String, dynamic>? _queueStatus;
  bool _isLoading = true;
  String? _error;
  StreamSubscription<Map<String, dynamic>>? _wsSubscription;
  int? _doctorId;

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
      // In a real app, you'd fetch the doctor record to get the doctor ID
      // For now, we'll use the user ID as doctor ID
      _doctorId = user.id;
      await _loadData();
      _setupWebSocket();
    }
  }

  /// Load appointments and queue status
  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      if (_doctorId != null) {
        // Load today's appointments
        final appointments = await _appointmentService.getDoctorAppointments(_doctorId!);
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

        // Load queue status
        _queueStatus = await _appointmentService.getQueueStatus(_doctorId!);
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
        // Reload data to get updated queue and appointments
        _loadData();
      }
    } else if (event == 'appointment_status') {
      // Reload appointments to get updated status
      _loadData();
    }
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);
    final user = authProvider.currentUser;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Doctor Dashboard'),
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
        child: _buildBody(user?.name ?? 'Doctor'),
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
          _buildQueueStatus(),
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
                userName.isNotEmpty ? userName[0].toUpperCase() : 'D',
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
                    'Dr. $userName',
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
                icon: Icons.people,
                label: 'Manage Queue',
                color: Colors.purple,
                onTap: () {
                  Navigator.of(context).pushNamed('/doctor/queue-management');
                },
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildQuickActionCard(
                icon: Icons.medical_services,
                label: 'Start Consultation',
                color: Colors.green,
                onTap: () {
                  // Navigate to first patient in queue if available
                  if (_queueStatus != null) {
                    final patients = _queueStatus!['patients'] as List? ?? [];
                    if (patients.isNotEmpty) {
                      final firstPatient = patients[0] as Map<String, dynamic>;
                      final appointmentId = firstPatient['appointment_id'] as int?;
                      
                      if (appointmentId != null) {
                        // Find the appointment in today's appointments
                        final appointment = _todayAppointments.firstWhere(
                          (apt) => apt.id == appointmentId,
                          orElse: () => _todayAppointments.first,
                        );
                        
                        Navigator.of(context).pushNamed(
                          '/doctor/consultation',
                          arguments: {'appointment': appointment},
                        );
                      }
                    } else {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('No patients in queue'),
                        ),
                      );
                    }
                  }
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
                icon: Icons.person_search,
                label: 'View Patient',
                color: Colors.blue,
                onTap: () {
                  Navigator.of(context).pushNamed('/doctor/patient-search');
                },
              ),
            ),
            const SizedBox(width: 12),
            const Expanded(child: SizedBox.shrink()),
          ],
        ),
      ],
    );
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

  Widget _buildQueueStatus() {
    final queueLength = _queueStatus?['queue_length'] as int? ?? 0;
    final patients = _queueStatus?['patients'] as List? ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Current Queue',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
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
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: queueLength > 0 ? Colors.orange : Colors.green,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (queueLength == 0)
          _buildEmptyQueueState()
        else
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  ...patients.take(3).map((patient) {
                    final patientData = patient as Map<String, dynamic>;
                    final position = patientData['queue_position'] as int?;
                    final name = patientData['patient_name'] as String? ?? 'Patient';
                    final waitTime = patientData['estimated_wait_time'] as int? ?? 0;
                    
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12.0),
                      child: Row(
                        children: [
                          Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              color: position == 1 
                                  ? Colors.green.withOpacity(0.2)
                                  : Colors.grey.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Center(
                              child: Text(
                                '$position',
                                style: TextStyle(
                                  fontSize: 18,
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
                                    fontSize: 16,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                                Text(
                                  'Wait time: ~$waitTime min',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey[600],
                                  ),
                                ),
                              ],
                            ),
                          ),
                          if (position == 1)
                            ElevatedButton(
                              onPressed: () {
                                final appointmentId = patientData['appointment_id'] as int?;
                                if (appointmentId != null) {
                                  // Find the appointment in today's appointments
                                  final appointment = _todayAppointments.firstWhere(
                                    (apt) => apt.id == appointmentId,
                                    orElse: () => _todayAppointments.isNotEmpty 
                                        ? _todayAppointments.first 
                                        : throw Exception('No appointment found'),
                                  );
                                  
                                  Navigator.of(context).pushNamed(
                                    '/doctor/consultation',
                                    arguments: {'appointment': appointment},
                                  );
                                }
                              },
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.green,
                                foregroundColor: Colors.white,
                              ),
                              child: const Text('Start'),
                            ),
                        ],
                      ),
                    );
                  }),
                  if (patients.length > 3)
                    TextButton(
                      onPressed: () {
                        Navigator.of(context).pushNamed('/doctor/queue-management');
                      },
                      child: Text('View all ${patients.length} patients'),
                    ),
                ],
              ),
            ),
          ),
      ],
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
              'You\'re all caught up!',
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
            const SizedBox(height: 8),
            Text(
              'Enjoy your day!',
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
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: () => _showAppointmentDetails(appointment),
                  child: const Text('Details'),
                ),
                const SizedBox(width: 8),
                if (appointment.isCheckedIn || appointment.queuePosition == 1)
                  ElevatedButton(
                    onPressed: () {
                      Navigator.of(context).pushNamed(
                        '/doctor/consultation',
                        arguments: {'appointment': appointment},
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      foregroundColor: Colors.white,
                    ),
                    child: const Text('Start Consultation'),
                  ),
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
      case 'no_show':
        color = Colors.red;
        label = 'No-Show';
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

  void _showAppointmentDetails(Appointment appointment) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Appointment Details'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildDetailRow('Patient', appointment.patientName ?? 'N/A'),
            _buildDetailRow('Date', DateFormatter.formatDate(appointment.scheduledTime)),
            _buildDetailRow('Time', DateFormatter.formatTime(appointment.scheduledTime)),
            _buildDetailRow('Status', appointment.status),
            _buildDetailRow('Type', appointment.appointmentType),
            if (appointment.queuePosition != null)
              _buildDetailRow('Queue Position', '${appointment.queuePosition}'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              '$label:',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          Expanded(
            child: Text(value),
          ),
        ],
      ),
    );
  }
}
