import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../services/admin_service.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';
import 'anomaly_alerts_screen.dart';

/// Admin home screen displaying system statistics and recent activity
class AdminHomeScreen extends StatefulWidget {
  const AdminHomeScreen({super.key});

  @override
  State<AdminHomeScreen> createState() => _AdminHomeScreenState();
}

class _AdminHomeScreenState extends State<AdminHomeScreen> {
  final AdminService _adminService = AdminService();
  
  Map<String, dynamic>? _statistics;
  Map<String, dynamic>? _recentActivity;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
  }

  /// Load dashboard data (statistics and recent activity)
  Future<void> _loadDashboardData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final statistics = await _adminService.getSystemStatistics();
      final recentActivity = await _adminService.getRecentActivity();
      
      setState(() {
        _statistics = statistics;
        _recentActivity = recentActivity;
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
    final authProvider = Provider.of<AuthProvider>(context);
    final user = authProvider.currentUser;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin Dashboard'),
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
        onRefresh: _loadDashboardData,
        child: _buildBody(user?.name ?? 'Admin'),
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
        onRetry: _loadDashboardData,
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
          _buildSystemStatistics(),
          const SizedBox(height: 24),
          _buildQuickLinks(),
          const SizedBox(height: 24),
          _buildRecentActivity(),
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
                userName.isNotEmpty ? userName[0].toUpperCase() : 'A',
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
                  Text(
                    'Administrator',
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
      ),
    );
  }

  Widget _buildSystemStatistics() {
    if (_statistics == null) return const SizedBox.shrink();

    final totalUsers = _statistics!['total_users'] as int? ?? 0;
    final appointmentsToday = _statistics!['appointments_today'] as int? ?? 0;
    final activeDoctors = _statistics!['active_doctors'] as int? ?? 0;
    final pendingAppointments = _statistics!['pending_appointments'] as int? ?? 0;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'System Statistics',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildStatCard(
                icon: Icons.people,
                label: 'Total Users',
                value: '$totalUsers',
                color: Colors.blue,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildStatCard(
                icon: Icons.calendar_today,
                label: 'Appointments Today',
                value: '$appointmentsToday',
                color: Colors.green,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildStatCard(
                icon: Icons.medical_services,
                label: 'Active Doctors',
                value: '$activeDoctors',
                color: Colors.purple,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildStatCard(
                icon: Icons.pending_actions,
                label: 'Pending Appointments',
                value: '$pendingAppointments',
                color: Colors.orange,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Icon(
                  icon,
                  size: 32,
                  color: color,
                ),
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickLinks() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Quick Links',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildQuickLinkCard(
                icon: Icons.people_alt,
                label: 'User Management',
                color: Colors.blue,
                onTap: () {
                  Navigator.of(context).pushNamed('/admin/user-management');
                },
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildQuickLinkCard(
                icon: Icons.security,
                label: 'Audit Dashboard',
                color: Colors.red,
                onTap: () {
                  Navigator.of(context).pushNamed('/admin/audit-dashboard');
                },
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildQuickLinkCard(
                icon: Icons.shield,
                label: 'Security Alerts',
                color: Colors.deepOrange,
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => const AnomalyAlertsScreen(),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildQuickLinkCard(
                icon: Icons.business,
                label: 'Organizations',
                color: Colors.teal,
                onTap: () {
                  Navigator.of(context).pushNamed('/admin/organizations');
                },
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildQuickLinkCard(
                icon: Icons.badge,
                label: 'Providers',
                color: Colors.indigo,
                onTap: () {
                  Navigator.of(context).pushNamed('/admin/providers');
                },
              ),
            ),
            const SizedBox(width: 12),
            const Expanded(child: SizedBox()),
          ],
        ),
      ],
    );
  }

  Widget _buildQuickLinkCard({
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

  Widget _buildRecentActivity() {
    if (_recentActivity == null) return const SizedBox.shrink();

    final recentAppointments = _recentActivity!['recent_appointments'] as List? ?? [];
    final recentRegistrations = _recentActivity!['recent_registrations'] as List? ?? [];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Recent Activity',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 12),
        _buildRecentAppointmentsSection(recentAppointments),
        const SizedBox(height: 16),
        _buildRecentRegistrationsSection(recentRegistrations),
      ],
    );
  }

  Widget _buildRecentAppointmentsSection(List recentAppointments) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.event,
                  size: 20,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(width: 8),
                const Text(
                  'Recent Appointments',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (recentAppointments.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8.0),
                child: Text(
                  'No recent appointments',
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey[600],
                  ),
                ),
              )
            else
              ...recentAppointments.map((apt) {
                final patientName = apt['patient_name'] as String? ?? 'Patient';
                final doctorName = apt['doctor_name'] as String? ?? 'Doctor';
                final scheduledTime = DateTime.parse(apt['scheduled_time'] as String);
                final status = apt['status'] as String? ?? 'scheduled';
                
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '$patientName → Dr. $doctorName',
                              style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                            Text(
                              DateFormatter.formatDateTime(scheduledTime),
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey[600],
                              ),
                            ),
                          ],
                        ),
                      ),
                      _buildStatusBadge(status),
                    ],
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }

  Widget _buildRecentRegistrationsSection(List recentRegistrations) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.person_add,
                  size: 20,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(width: 8),
                const Text(
                  'Recent Registrations',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            if (recentRegistrations.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8.0),
                child: Text(
                  'No recent registrations',
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey[600],
                  ),
                ),
              )
            else
              ...recentRegistrations.map((user) {
                final name = user['name'] as String? ?? 'User';
                final email = user['email'] as String? ?? '';
                final role = user['role'] as String? ?? 'User';
                final createdAt = DateTime.parse(user['created_at'] as String);
                
                return Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: Row(
                    children: [
                      CircleAvatar(
                        radius: 16,
                        backgroundColor: _getRoleColor(role).withOpacity(0.2),
                        child: Text(
                          name.isNotEmpty ? name[0].toUpperCase() : 'U',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: _getRoleColor(role),
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
                              email,
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey[600],
                              ),
                            ),
                          ],
                        ),
                      ),
                      _buildRoleBadge(role),
                    ],
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusBadge(String status) {
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
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color, width: 1),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w600,
          color: color,
        ),
      ),
    );
  }

  Widget _buildRoleBadge(String role) {
    final color = _getRoleColor(role);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color, width: 1),
      ),
      child: Text(
        role,
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w600,
          color: color,
        ),
      ),
    );
  }

  Color _getRoleColor(String role) {
    switch (role) {
      case 'Admin':
        return Colors.red;
      case 'Doctor':
        return Colors.purple;
      case 'Nurse':
        return Colors.green;
      case 'Patient':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }
}
