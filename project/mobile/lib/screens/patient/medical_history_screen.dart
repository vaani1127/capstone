import 'package:flutter/material.dart';
import '../../models/medical_record.dart';
import '../../services/medical_record_service.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';

/// Medical history screen displaying consultations and prescriptions.
///
/// When [patientId] is provided (doctor viewing a specific patient), the screen
/// loads that patient's records via GET /medical-records/patient/{id} and shows
/// [patientName] in the title. When both are null (patient viewing their own
/// records), it calls GET /medical-records/me as before.
class MedicalHistoryScreen extends StatefulWidget {
  final int? patientId;
  final String? patientName;

  const MedicalHistoryScreen({super.key, this.patientId, this.patientName});

  @override
  State<MedicalHistoryScreen> createState() => _MedicalHistoryScreenState();
}

class _MedicalHistoryScreenState extends State<MedicalHistoryScreen> {
  final MedicalRecordService _medicalRecordService = MedicalRecordService();
  
  List<MedicalRecord> _records = [];
  bool _isLoading = true;
  String? _error;
  String _filterType = 'all'; // all, consultations, prescriptions

  @override
  void initState() {
    super.initState();
    _loadMedicalRecords();
  }

  /// Load medical records from API.
  ///
  /// Uses the patient-specific endpoint when [widget.patientId] is set
  /// (doctor viewing a patient), otherwise loads the current user's own records.
  Future<void> _loadMedicalRecords() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final List<MedicalRecord> records;
      if (widget.patientId != null) {
        records = await _medicalRecordService.getPatientRecords(widget.patientId!);
      } else {
        records = await _medicalRecordService.getMyMedicalRecords();
      }
      setState(() {
        _records = records
          ..sort((a, b) => b.createdAt.compareTo(a.createdAt)); // Newest first
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  /// Get filtered records based on selected filter
  List<MedicalRecord> get _filteredRecords {
    switch (_filterType) {
      case 'consultations':
        return _records.where((r) => r.hasConsultationNotes).toList();
      case 'prescriptions':
        return _records.where((r) => r.hasPrescription).toList();
      default:
        return _records;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.patientName != null
              ? '${widget.patientName}\'s Records'
              : 'Medical History',
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: _showFilterDialog,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadMedicalRecords,
        child: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading medical records...');
    }

    if (_error != null) {
      return ErrorMessage(
        message: _error!,
        onRetry: _loadMedicalRecords,
      );
    }

    final filteredRecords = _filteredRecords;

    if (filteredRecords.isEmpty) {
      return _buildEmptyState();
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16.0),
      itemCount: filteredRecords.length,
      itemBuilder: (context, index) {
        return _buildRecordCard(filteredRecords[index]);
      },
    );
  }

  Widget _buildEmptyState() {
    String message;
    switch (_filterType) {
      case 'consultations':
        message = 'No consultation records found';
        break;
      case 'prescriptions':
        message = 'No prescription records found';
        break;
      default:
        message = 'No medical records found';
    }

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.medical_information_outlined,
              size: 64,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 16),
            Text(
              message,
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Your medical records will appear here',
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

  Widget _buildRecordCard(MedicalRecord record) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () => _showRecordDetails(record),
        borderRadius: BorderRadius.circular(12),
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
                          record.doctorName ?? 'Doctor',
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
                              DateFormatter.formatDate(record.createdAt),
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
                              DateFormatter.formatTime(record.createdAt),
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
                  if (record.isTampered == true)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.red.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.red),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.warning, size: 14, color: Colors.red),
                          SizedBox(width: 4),
                          Text(
                            'Tampered',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                              color: Colors.red,
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  if (record.hasConsultationNotes)
                    _buildRecordTypeChip(
                      icon: Icons.note_alt,
                      label: 'Consultation',
                      color: Colors.blue,
                    ),
                  if (record.hasConsultationNotes && record.hasPrescription)
                    const SizedBox(width: 8),
                  if (record.hasPrescription)
                    _buildRecordTypeChip(
                      icon: Icons.medication,
                      label: 'Prescription',
                      color: Colors.green,
                    ),
                ],
              ),
              if (record.diagnosis != null) ...[
                const SizedBox(height: 12),
                Text(
                  'Diagnosis: ${record.diagnosis}',
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey[700],
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  if (!record.isOriginal)
                    Text(
                      'Version ${record.versionNumber}',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  Row(
                    children: [
                      TextButton.icon(
                        onPressed: () => _showVersionHistory(record),
                        icon: const Icon(Icons.history, size: 16),
                        label: const Text('History'),
                      ),
                      const SizedBox(width: 8),
                      TextButton(
                        onPressed: () => _showRecordDetails(record),
                        child: const Text('View Details'),
                      ),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRecordTypeChip({
    required IconData icon,
    required String label,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
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

  void _showFilterDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Filter Records'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            RadioListTile<String>(
              title: const Text('All Records'),
              value: 'all',
              groupValue: _filterType,
              onChanged: (value) {
                setState(() {
                  _filterType = value!;
                });
                Navigator.of(context).pop();
              },
            ),
            RadioListTile<String>(
              title: const Text('Consultations Only'),
              value: 'consultations',
              groupValue: _filterType,
              onChanged: (value) {
                setState(() {
                  _filterType = value!;
                });
                Navigator.of(context).pop();
              },
            ),
            RadioListTile<String>(
              title: const Text('Prescriptions Only'),
              value: 'prescriptions',
              groupValue: _filterType,
              onChanged: (value) {
                setState(() {
                  _filterType = value!;
                });
                Navigator.of(context).pop();
              },
            ),
          ],
        ),
      ),
    );
  }

  void _showRecordDetails(MedicalRecord record) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            const Text('Record Details'),
            if (record.isTampered == true) ...[
              const SizedBox(width: 8),
              const Icon(Icons.warning, color: Colors.red, size: 20),
            ],
          ],
        ),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildDetailSection('Doctor', record.doctorName ?? 'N/A'),
              _buildDetailSection('Date', DateFormatter.formatDate(record.createdAt)),
              _buildDetailSection('Time', DateFormatter.formatTime(record.createdAt)),
              _buildDetailSection('Version', '${record.versionNumber}'),
              if (record.diagnosis != null)
                _buildDetailSection('Diagnosis', record.diagnosis!),
              if (record.consultationNotes != null) ...[
                const Divider(height: 24),
                const Text(
                  'Consultation Notes',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Text(record.consultationNotes!),
              ],
              if (record.prescription != null) ...[
                const Divider(height: 24),
                const Text(
                  'Prescription',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                Text(record.prescription!),
              ],
              if (record.isTampered == true) ...[
                const Divider(height: 24),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.red.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.red),
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.warning, color: Colors.red),
                      SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          'This record has been flagged as potentially tampered',
                          style: TextStyle(
                            color: Colors.red,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
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

  Widget _buildDetailSection(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: Colors.grey,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: const TextStyle(fontSize: 14),
          ),
        ],
      ),
    );
  }

  Future<void> _showVersionHistory(MedicalRecord record) async {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Loading version history...'),
        content: const SizedBox(
          height: 100,
          child: Center(child: CircularProgressIndicator()),
        ),
      ),
    );

    try {
      final versions = await _medicalRecordService.getRecordVersions(record.id);
      
      if (!mounted) return;
      
      Navigator.of(context).pop(); // Close loading dialog
      
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Version History'),
          content: SizedBox(
            width: double.maxFinite,
            child: versions.isEmpty
                ? const Padding(
                    padding: EdgeInsets.all(16.0),
                    child: Text('No version history available'),
                  )
                : ListView.builder(
                    shrinkWrap: true,
                    itemCount: versions.length,
                    itemBuilder: (context, index) {
                      final version = versions[index];
                      return Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: version.versionNumber == record.versionNumber
                                ? Theme.of(context).colorScheme.primary
                                : Colors.grey,
                            child: Text(
                              'v${version.versionNumber}',
                              style: const TextStyle(
                                fontSize: 12,
                                color: Colors.white,
                              ),
                            ),
                          ),
                          title: Text(
                            DateFormatter.formatDate(version.createdAt),
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          subtitle: Text(
                            DateFormatter.formatTime(version.createdAt),
                          ),
                          trailing: version.versionNumber == record.versionNumber
                              ? const Chip(
                                  label: Text(
                                    'Current',
                                    style: TextStyle(fontSize: 10),
                                  ),
                                  padding: EdgeInsets.symmetric(horizontal: 8),
                                )
                              : null,
                          onTap: () {
                            Navigator.of(context).pop();
                            _showRecordDetails(version);
                          },
                        ),
                      );
                    },
                  ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    } catch (e) {
      if (!mounted) return;
      
      Navigator.of(context).pop(); // Close loading dialog
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to load version history: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
}
