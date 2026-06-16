import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/appointment.dart';
import '../../models/allergy.dart';
import '../../providers/auth_provider.dart';
import '../../services/medical_record_service.dart';
import '../../services/api_client.dart';
import '../../services/allergy_service.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';

/// Consultation screen for doctors to document consultations and create prescriptions
class ConsultationScreen extends StatefulWidget {
  final Appointment appointment;

  const ConsultationScreen({
    super.key,
    required this.appointment,
  });

  @override
  State<ConsultationScreen> createState() => _ConsultationScreenState();
}

class _ConsultationScreenState extends State<ConsultationScreen> {
  final MedicalRecordService _medicalRecordService = MedicalRecordService();
  final ApiClient _apiClient = ApiClient();
  final _formKey = GlobalKey<FormState>();
  
  final _symptomsController = TextEditingController();
  final _diagnosisController = TextEditingController();
  final _observationsController = TextEditingController();
  final _medicationController = TextEditingController();
  final _dosageController = TextEditingController();
  final _frequencyController = TextEditingController();
  final _durationController = TextEditingController();
  
  bool _isLoading = false;
  bool _isSaving = false;
  String? _error;
  Map<String, dynamic>? _patientInfo;

  @override
  void initState() {
    super.initState();
    _loadPatientInfo();
  }

  @override
  void dispose() {
    _symptomsController.dispose();
    _diagnosisController.dispose();
    _observationsController.dispose();
    _medicationController.dispose();
    _dosageController.dispose();
    _frequencyController.dispose();
    _durationController.dispose();
    super.dispose();
  }

  /// Load patient information
  Future<void> _loadPatientInfo() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // Fetch patient details from API
      final response = await _apiClient.get('/users/${widget.appointment.patientId}');
      setState(() {
        _patientInfo = response;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  /// Save consultation and complete appointment
  Future<void> _saveConsultation() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isSaving = true;
    });

    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);
      final user = authProvider.currentUser;

      if (user == null) {
        throw Exception('User not authenticated');
      }

      // Build consultation notes
      final consultationNotes = '''
Symptoms: ${_symptomsController.text.trim()}

Observations: ${_observationsController.text.trim()}
'''.trim();

      // Create consultation note
      await _medicalRecordService.createConsultationNote(
        patientId: widget.appointment.patientId,
        appointmentId: widget.appointment.id,
        consultationNotes: consultationNotes,
        diagnosis: _diagnosisController.text.trim(),
      );

      // Create prescription if medication is provided
      if (_medicationController.text.trim().isNotEmpty) {
        final prescription = '''
Medication: ${_medicationController.text.trim()}
Dosage: ${_dosageController.text.trim()}
Frequency: ${_frequencyController.text.trim()}
Duration: ${_durationController.text.trim()}
'''.trim();

        await _medicalRecordService.createPrescription(
          patientId: widget.appointment.patientId,
          appointmentId: widget.appointment.id,
          prescription: prescription,
        );
      }

      // Update appointment status to completed
      await _apiClient.patch('/appointments/${widget.appointment.id}/status', {
        'status': 'completed',
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Consultation saved successfully'),
            backgroundColor: Colors.green,
          ),
        );

        // Navigate back to doctor home
        Navigator.of(context).popUntil((route) => route.isFirst);
      }
    } catch (e) {
      setState(() {
        _isSaving = false;
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to save consultation: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Consultation'),
        actions: [
          IconButton(
            icon: const Icon(Icons.warning_amber_rounded),
            tooltip: 'Allergies',
            onPressed: () => Navigator.of(context).pushNamed(
              '/allergies',
              arguments: {
                'patientId': widget.appointment.patientId,
                'patientName': widget.appointment.patientName ?? 'Patient',
              },
            ),
          ),
          if (!_isSaving)
            TextButton.icon(
              onPressed: _saveConsultation,
              icon: const Icon(Icons.save, color: Colors.white),
              label: const Text(
                'Save & Complete',
                style: TextStyle(color: Colors.white),
              ),
            ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading patient information...');
    }

    if (_error != null) {
      return ErrorMessage(
        message: _error!,
        onRetry: _loadPatientInfo,
      );
    }

    return Stack(
      children: [
        SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildPatientInfoCard(),
                const SizedBox(height: 24),
                _AllergyBanner(patientId: widget.appointment.patientId),
                _buildConsultationNotesSection(),
                const SizedBox(height: 24),
                _buildPrescriptionSection(),
                const SizedBox(height: 24),
                _buildSaveButton(),
                const SizedBox(height: 16),
              ],
            ),
          ),
        ),
        if (_isSaving)
          Container(
            color: Colors.black54,
            child: const LoadingIndicator(message: 'Saving consultation...'),
          ),
      ],
    );
  }

  Widget _buildPatientInfoCard() {
    final patientName = widget.appointment.patientName ?? 'Patient';
    final patientEmail = _patientInfo?['email'] as String? ?? 'N/A';
    
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 30,
                  backgroundColor: Theme.of(context).colorScheme.primary,
                  child: Text(
                    patientName.isNotEmpty ? patientName[0].toUpperCase() : 'P',
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
                        patientName,
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        patientEmail,
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const Divider(height: 24),
            _buildInfoRow('Appointment ID', '#${widget.appointment.id}'),
            _buildInfoRow('Type', widget.appointment.isWalkIn ? 'Walk-in' : 'Scheduled'),
            _buildInfoRow('Scheduled Time', DateFormatter.formatDateTime(widget.appointment.scheduledTime)),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.grey[700],
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConsultationNotesSection() {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.medical_services,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(width: 8),
                const Text(
                  'Consultation Notes',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _symptomsController,
              decoration: const InputDecoration(
                labelText: 'Symptoms',
                hintText: 'Enter patient symptoms',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.sick),
              ),
              maxLines: 3,
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Please enter symptoms';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _observationsController,
              decoration: const InputDecoration(
                labelText: 'Observations',
                hintText: 'Enter clinical observations',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.visibility),
              ),
              maxLines: 3,
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Please enter observations';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _diagnosisController,
              decoration: const InputDecoration(
                labelText: 'Diagnosis',
                hintText: 'Enter diagnosis',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.assignment),
              ),
              maxLines: 2,
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Please enter diagnosis';
                }
                return null;
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPrescriptionSection() {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.medication,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(width: 8),
                const Text(
                  'Prescription',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Optional - Leave blank if no medication required',
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _medicationController,
              decoration: const InputDecoration(
                labelText: 'Medication Name',
                hintText: 'e.g., Paracetamol',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.local_pharmacy),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _dosageController,
                    decoration: const InputDecoration(
                      labelText: 'Dosage',
                      hintText: 'e.g., 500mg',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextFormField(
                    controller: _frequencyController,
                    decoration: const InputDecoration(
                      labelText: 'Frequency',
                      hintText: 'e.g., 3 times/day',
                      border: OutlineInputBorder(),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _durationController,
              decoration: const InputDecoration(
                labelText: 'Duration',
                hintText: 'e.g., 5 days',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.calendar_today),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSaveButton() {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: _isSaving ? null : _saveConsultation,
        icon: const Icon(Icons.save),
        label: const Text('Save & Complete Consultation'),
        style: ElevatedButton.styleFrom(
          padding: const EdgeInsets.symmetric(vertical: 16),
          backgroundColor: Colors.green,
          foregroundColor: Colors.white,
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}


// ---------------------------------------------------------------------------
// Allergy safety banner
// ---------------------------------------------------------------------------

/// Loads active severe allergies for [patientId] on mount and displays a red
/// warning banner when any are found.  Returns [SizedBox.shrink] silently if
/// the API call fails or if no severe allergies exist — this widget must never
/// block or crash the consultation workflow.
class _AllergyBanner extends StatefulWidget {
  final int patientId;

  const _AllergyBanner({required this.patientId});

  @override
  State<_AllergyBanner> createState() => _AllergyBannerState();
}

class _AllergyBannerState extends State<_AllergyBanner> {
  final AllergyService _service = AllergyService();
  List<String> _severeAllergens = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final allergies = await _service.getPatientAllergies(widget.patientId);
      if (!mounted) return;
      final severe = allergies
          .where((a) => a.isActive && a.severity == 'severe')
          .map((a) => a.allergen)
          .toList();
      if (severe.isNotEmpty) {
        setState(() => _severeAllergens = severe);
      }
    } catch (_) {
      // Silent failure — safety feature must not interfere with consultation.
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_severeAllergens.isEmpty) return const SizedBox.shrink();

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.red.shade50,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.red.shade400, width: 1.5),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.warning_amber_rounded,
              color: Colors.red.shade700, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'SEVERE ALLERGY ALERT',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.red.shade800,
                    fontSize: 13,
                    letterSpacing: 0.4,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  _severeAllergens.join(' • '),
                  style: TextStyle(
                    color: Colors.red.shade700,
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
