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

/// Patient home screen displaying appointments, quick actions, and notifications
class PatientHomeScreen extends StatefulWidget {
  const PatientHomeScreen({super.key});

  @override
  State<PatientHomeScreen> createState() => _PatientHomeScreenState();
}

class _PatientHomeScreenState extends State<PatientHomeScreen> {
  final AppointmentService _appointmentService = AppointmentService();
  final WebSocketService _wsService = WebSocketService();
  
  List<Appointment> _appointments = [];
  bool _isLoading = true;
  String? _error;
  final List<String> _notifications = [];
  StreamSubscription<Map<String, dynamic>>? _wsSubscription;

  @override
  void initState() {
    super.initState();
    _loadAppointments();
    _setupWebSocket();
  }

  @override
  void dispose() {
    _wsSubscription?.cancel();
    super.dispose();
  }

  /// Load appointments from API
  Future<void> _loadAppointments() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final appointments = await _appointmentService.getAppointments();
      setState(() {
        _appointments = appointments
            .where((apt) => !apt.isCancelled && !apt.isCompleted)
            .toList()
          ..sort((a, b) => a.scheduledTime.compareTo(b.scheduledTime));
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
    
    if (event == 'appointment_status') {
      final data = message['data'] as Map<String, dynamic>;
      final appointmentId = data['appointment_id'] as int;
      final status = data['status'] as String;
      
      // Update appointment in list
      setState(() {
        final index = _appointments.indexWhere((apt) => apt.id == appointmentId);
        if (index != -1) {
          // Reload appointments to get updated data
          _loadAppointments();
          
          // Add notification
          _notifications.insert(0, 'Appointment status updated to: $status');
          if (_notifications.length > 5) {
            _notifications.removeLast();
          }
        }
      });
    } else if (event == 'queue_update') {
      // Reload appointments to get updated queue positions
      _loadAppointments();
    }
  }

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);
    final user = authProvider.currentUser;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Home'),
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
        onRefresh: _loadAppointments,
        child: _buildBody(user?.name ?? 'Patient'),
      ),
    );
  }

  Widget _buildBody(String userName) {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading appointments...');
    }

    if (_error != null) {
      return ErrorMessage(
        message: _error!,
        onRetry: _loadAppointments,
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
          if (_notifications.isNotEmpty) ...[
            _buildNotificationsSection(),
            const SizedBox(height: 24),
          ],
          _buildUpcomingAppointments(),
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
                userName.isNotEmpty ? userName[0].toUpperCase() : 'P',
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
                icon: Icons.calendar_today,
                label: 'Book Appointment',
                color: Colors.blue,
                onTap: () {
                  Navigator.of(context).pushNamed('/appointment-booking');
                },
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildQuickActionCard(
                icon: Icons.history,
                label: 'Medical History',
                color: Colors.green,
                onTap: () {
                  Navigator.of(context).pushNamed('/medical-history');
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
                label: 'My Vitals',
                color: Colors.red,
                onTap: () {
                  // patientId omitted — VitalsHistoryScreen calls GET /vitals/me
                  Navigator.of(context).pushNamed('/vitals/history');
                },
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildQuickActionCard(
                icon: Icons.medical_services,
                label: 'My Procedures',
                color: Colors.purple,
                onTap: () {
                  // patientId omitted — ProceduresScreen calls GET /procedures/me
                  Navigator.of(context).pushNamed('/procedures');
                },
              ),
            ),
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

  Widget _buildNotificationsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Notifications',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            if (_notifications.isNotEmpty)
              TextButton(
                onPressed: () {
                  setState(() {
                    _notifications.clear();
                  });
                },
                child: const Text('Clear All'),
              ),
          ],
        ),
        const SizedBox(height: 8),
        ..._notifications.map((notification) => Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            leading: Icon(
              Icons.notifications,
              color: Theme.of(context).colorScheme.primary,
            ),
            title: Text(notification),
            dense: true,
          ),
        )),
      ],
    );
  }

  Widget _buildUpcomingAppointments() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Upcoming Appointments',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        if (_appointments.isEmpty)
          _buildEmptyState()
        else
          ..._appointments.map((appointment) => _buildAppointmentCard(appointment)),
      ],
    );
  }

  Widget _buildEmptyState() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          children: [
            Icon(
              Icons.event_busy,
              size: 64,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 16),
            Text(
              'No upcoming appointments',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Book an appointment to get started',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[500],
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: () {
                Navigator.of(context).pushNamed('/appointment-booking');
              },
              icon: const Icon(Icons.add),
              label: const Text('Book Appointment'),
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
                        appointment.doctorName ?? 'Doctor',
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Icon(
                            Icons.calendar_today,
                            size: 14,
                            color: Colors.grey[600],
                          ),
                          const SizedBox(width: 4),
                          Text(
                            DateFormatter.formatDate(appointment.scheduledTime),
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey[600],
                            ),
                          ),
                          const SizedBox(width: 12),
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
                TextButton.icon(
                  onPressed: () {
                    Navigator.of(context).pushNamed(
                      '/queue-status',
                      arguments: {
                        'doctorId': appointment.doctorId,
                        'doctorName': appointment.doctorName,
                      },
                    );
                  },
                  icon: const Icon(Icons.people, size: 16),
                  label: const Text('View Queue'),
                ),
                const SizedBox(width: 8),
                TextButton(
                  onPressed: () => _showAppointmentDetails(appointment),
                  child: const Text('Details'),
                ),
                const SizedBox(width: 8),
                if (appointment.isScheduled && 
                    appointment.scheduledTime.difference(DateTime.now()).inHours > 2)
                  TextButton(
                    onPressed: () => _cancelAppointment(appointment),
                    style: TextButton.styleFrom(
                      foregroundColor: Colors.red,
                    ),
                    child: const Text('Cancel'),
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
            _buildDetailRow('Doctor', appointment.doctorName ?? 'N/A'),
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

  Future<void> _cancelAppointment(Appointment appointment) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cancel Appointment'),
        content: const Text('Are you sure you want to cancel this appointment?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('No'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: TextButton.styleFrom(
              foregroundColor: Colors.red,
            ),
            child: const Text('Yes, Cancel'),
          ),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      try {
        await _appointmentService.cancelAppointment(appointment.id);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Appointment cancelled successfully'),
              backgroundColor: Colors.green,
            ),
          );
          _loadAppointments();
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Failed to cancel appointment: $e'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    }
  }
}
