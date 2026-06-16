import 'dart:async';
import 'package:flutter/material.dart';
import '../../services/admin_service.dart';
import '../../services/api_client.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';

/// Audit dashboard screen displaying audit logs and tampering alerts
class AuditDashboardScreen extends StatefulWidget {
  const AuditDashboardScreen({super.key});

  @override
  State<AuditDashboardScreen> createState() => _AuditDashboardScreenState();
}

class _AuditDashboardScreenState extends State<AuditDashboardScreen> {
  final AdminService _adminService = AdminService();
  
  List<Map<String, dynamic>> _auditLogs = [];
  List<Map<String, dynamic>> _tamperingAlerts = [];
  bool _isLoading = true;
  String? _error;
  
  // Pagination
  int _currentPage = 1;
  int _totalPages = 1;
  int _totalLogs = 0;
  final int _pageSize = 20;
  
  // Filters
  DateTimeRange? _dateRange;
  int? _selectedUserId;
  String? _selectedRecordType;
  
  @override
  void initState() {
    super.initState();
    _loadAuditData();
  }

  /// Verify the full SHA-256 hash chain and show results in a dialog
  Future<void> _verifyChainIntegrity() async {
    try {
      final result = await ApiClient().get('/audit/chain-integrity');
      final isValid = result['is_valid'] as bool;
      final total = result['total_blocks'] as int;
      final verified = result['verified_blocks'] as int;
      final issues = result['inconsistencies'] as List? ?? [];

      if (!mounted) return;
      showDialog(
        context: context,
        builder: (_) => AlertDialog(
          title: Row(children: [
            Icon(isValid ? Icons.check_circle : Icons.error,
                color: isValid ? Colors.green : Colors.red),
            const SizedBox(width: 8),
            Text(isValid ? 'Chain Valid' : 'Chain Compromised'),
          ]),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Total blocks: $total'),
              Text('Verified: $verified'),
              if (issues.isNotEmpty) ...[
                const SizedBox(height: 8),
                const Text('Inconsistencies:',
                    style: TextStyle(fontWeight: FontWeight.bold)),
                ...issues.map((e) => Text('• $e')),
              ],
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to verify chain integrity')),
      );
    }
  }

  /// Load audit logs and tampering alerts
  Future<void> _loadAuditData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final logsData = await _adminService.getAuditLogs(
        page: _currentPage,
        pageSize: _pageSize,
        startDate: _dateRange?.start,
        endDate: _dateRange?.end,
        userId: _selectedUserId,
        recordType: _selectedRecordType,
      );
      
      final alerts = await _adminService.getTamperingAlerts();
      
      setState(() {
        _auditLogs = List<Map<String, dynamic>>.from(
          (logsData['logs'] as List).map((e) => Map<String, dynamic>.from(e as Map)),
        );
        _totalLogs = logsData['total'] as int;
        _totalPages = logsData['total_pages'] as int;
        _tamperingAlerts = List<Map<String, dynamic>>.from(
          alerts.map((e) => Map<String, dynamic>.from(e)),
        );
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  /// Show date range picker
  Future<void> _selectDateRange() async {
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
      initialDateRange: _dateRange,
    );
    
    if (picked != null) {
      setState(() {
        _dateRange = picked;
        _currentPage = 1;
      });
      _loadAuditData();
    }
  }

  /// Clear all filters
  void _clearFilters() {
    setState(() {
      _dateRange = null;
      _selectedUserId = null;
      _selectedRecordType = null;
      _currentPage = 1;
    });
    _loadAuditData();
  }

  /// Export audit logs
  Future<void> _exportLogs(String format) async {
    try {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Exporting audit logs as $format...')),
      );
      
      await _adminService.exportAuditLogs(
        format: format,
        startDate: _dateRange?.start,
        endDate: _dateRange?.end,
        userId: _selectedUserId,
        recordType: _selectedRecordType,
      );
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Audit logs exported successfully as $format')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to export: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Audit Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.verified_user_outlined),
            tooltip: 'Verify Chain Integrity',
            onPressed: _verifyChainIntegrity,
          ),
          PopupMenuButton<String>(
            icon: const Icon(Icons.download),
            tooltip: 'Export Logs',
            onSelected: _exportLogs,
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'json',
                child: Row(
                  children: [
                    Icon(Icons.code),
                    SizedBox(width: 8),
                    Text('Export as JSON'),
                  ],
                ),
              ),
              const PopupMenuItem(
                value: 'csv',
                child: Row(
                  children: [
                    Icon(Icons.table_chart),
                    SizedBox(width: 8),
                    Text('Export as CSV'),
                  ],
                ),
              ),
            ],
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadAuditData,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadAuditData,
        child: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading audit data...');
    }

    if (_error != null) {
      return ErrorMessage(
        message: _error!,
        onRetry: _loadAuditData,
      );
    }

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildTamperingAlerts(),
          const SizedBox(height: 24),
          _buildFilters(),
          const SizedBox(height: 16),
          _buildAuditLogs(),
          const SizedBox(height: 16),
          _buildPagination(),
        ],
      ),
    );
  }

  Widget _buildTamperingAlerts() {
    if (_tamperingAlerts.isEmpty) {
      return Card(
        color: Colors.green.shade50,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            children: [
              Icon(
                Icons.check_circle,
                color: Colors.green.shade700,
                size: 32,
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'No Tampering Detected',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.green.shade900,
                      ),
                    ),
                    Text(
                      'All records are secure and verified',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.green.shade700,
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

    return Card(
      color: Colors.red.shade50,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.warning,
                  color: Colors.red.shade700,
                  size: 32,
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Tampering Alerts',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.red.shade900,
                        ),
                      ),
                      Text(
                        '${_tamperingAlerts.length} record(s) flagged for tampering',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.red.shade700,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ..._tamperingAlerts.take(3).map((alert) => _buildTamperingAlertItem(alert)),
            if (_tamperingAlerts.length > 3)
              Padding(
                padding: const EdgeInsets.only(top: 8.0),
                child: Text(
                  'And ${_tamperingAlerts.length - 3} more...',
                  style: TextStyle(
                    fontSize: 12,
                    fontStyle: FontStyle.italic,
                    color: Colors.red.shade700,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildTamperingAlertItem(Map<String, dynamic> alert) {
    final recordType = alert['record_type'] as String? ?? 'Unknown';
    final recordId = alert['record_id'] as int? ?? 0;
    final timestamp = DateTime.parse(alert['timestamp'] as String);
    final userName = alert['user_name'] as String? ?? 'Unknown User';

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.red.shade300),
      ),
      child: Row(
        children: [
          Icon(
            Icons.error_outline,
            color: Colors.red.shade700,
            size: 20,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$recordType #$recordId',
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Modified by $userName',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  ),
                ),
                Text(
                  DateFormatter.formatDateTime(timestamp),
                  style: TextStyle(
                    fontSize: 11,
                    color: Colors.grey[500],
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilters() {
    final hasActiveFilters = _dateRange != null || 
        _selectedUserId != null || 
        _selectedRecordType != null;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Filters',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (hasActiveFilters)
                  TextButton.icon(
                    onPressed: _clearFilters,
                    icon: const Icon(Icons.clear, size: 16),
                    label: const Text('Clear All'),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                // Date range filter
                FilterChip(
                  label: Text(
                    _dateRange == null
                        ? 'Date Range'
                        : '${DateFormatter.formatDate(_dateRange!.start)} - ${DateFormatter.formatDate(_dateRange!.end)}',
                  ),
                  selected: _dateRange != null,
                  onSelected: (_) => _selectDateRange(),
                  avatar: const Icon(Icons.calendar_today, size: 16),
                ),
                // Record type filter
                DropdownButton<String>(
                  value: _selectedRecordType,
                  hint: const Text('Record Type'),
                  underline: const SizedBox(),
                  items: const [
                    DropdownMenuItem(value: null, child: Text('All Types')),
                    DropdownMenuItem(value: 'medical_record', child: Text('Medical Record')),
                    DropdownMenuItem(value: 'appointment', child: Text('Appointment')),
                  ],
                  onChanged: (value) {
                    setState(() {
                      _selectedRecordType = value;
                      _currentPage = 1;
                    });
                    _loadAuditData();
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAuditLogs() {
    if (_auditLogs.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Center(
            child: Column(
              children: [
                Icon(
                  Icons.history,
                  size: 64,
                  color: Colors.grey[400],
                ),
                const SizedBox(height: 16),
                Text(
                  'No audit logs found',
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

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Audit Logs',
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              'Total: $_totalLogs',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[600],
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        ..._auditLogs.map((log) => _buildAuditLogCard(log)),
      ],
    );
  }

  Widget _buildAuditLogCard(Map<String, dynamic> log) {
    final recordType = log['record_type'] as String? ?? 'Unknown';
    final recordId = log['record_id'] as int? ?? 0;
    final timestamp = DateTime.parse(log['timestamp'] as String);
    final userName = log['user_name'] as String? ?? 'Unknown User';
    final userEmail = log['user_email'] as String? ?? '';
    final hash = log['hash'] as String? ?? '';
    final isTampered = log['is_tampered'] as bool? ?? false;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ExpansionTile(
        leading: CircleAvatar(
          backgroundColor: isTampered 
              ? Colors.red.shade100 
              : _getRecordTypeColor(recordType).withOpacity(0.2),
          child: Icon(
            isTampered ? Icons.warning : _getRecordTypeIcon(recordType),
            color: isTampered ? Colors.red.shade700 : _getRecordTypeColor(recordType),
            size: 20,
          ),
        ),
        title: Text(
          '$recordType #$recordId',
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(
              userName,
              style: TextStyle(
                fontSize: 13,
                color: Colors.grey[700],
              ),
            ),
            Text(
              DateFormatter.formatDateTime(timestamp),
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[500],
              ),
            ),
          ],
        ),
        trailing: isTampered
            ? Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.red.shade100,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red.shade700, width: 1),
                ),
                child: Text(
                  'TAMPERED',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: Colors.red.shade700,
                  ),
                ),
              )
            : null,
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildDetailRow('Record ID', '$recordId'),
                _buildDetailRow('Record Type', recordType),
                _buildDetailRow('User', userName),
                _buildDetailRow('Email', userEmail),
                _buildDetailRow('Timestamp', DateFormatter.formatDateTime(timestamp)),
                _buildDetailRow('Hash', _truncateHash(hash)),
                if (isTampered)
                  Padding(
                    padding: const EdgeInsets.only(top: 8.0),
                    child: Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.red.shade50,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.red.shade300),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            Icons.warning,
                            color: Colors.red.shade700,
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'This record has been flagged for tampering. Hash verification failed.',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.red.shade900,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: Colors.grey[700],
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 13,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPagination() {
    if (_totalPages <= 1) return const SizedBox.shrink();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            IconButton(
              icon: const Icon(Icons.chevron_left),
              onPressed: _currentPage > 1
                  ? () {
                      setState(() {
                        _currentPage--;
                      });
                      _loadAuditData();
                    }
                  : null,
            ),
            Text(
              'Page $_currentPage of $_totalPages',
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
            IconButton(
              icon: const Icon(Icons.chevron_right),
              onPressed: _currentPage < _totalPages
                  ? () {
                      setState(() {
                        _currentPage++;
                      });
                      _loadAuditData();
                    }
                  : null,
            ),
          ],
        ),
      ),
    );
  }

  IconData _getRecordTypeIcon(String recordType) {
    switch (recordType) {
      case 'medical_record':
        return Icons.medical_services;
      case 'appointment':
        return Icons.event;
      default:
        return Icons.description;
    }
  }

  Color _getRecordTypeColor(String recordType) {
    switch (recordType) {
      case 'medical_record':
        return Colors.purple;
      case 'appointment':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  String _truncateHash(String hash) {
    if (hash.length <= 16) return hash;
    return '${hash.substring(0, 8)}...${hash.substring(hash.length - 8)}';
  }
}
