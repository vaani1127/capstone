import 'package:flutter/material.dart';
import '../../models/appointment.dart';
import '../../models/doctor.dart';
import '../../services/appointment_service.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';
import '../../utils/date_formatter.dart';

/// Walk-in registration screen for nurses to register walk-in patients
class WalkInRegistrationScreen extends StatefulWidget {
  const WalkInRegistrationScreen({super.key});

  @override
  State<WalkInRegistrationScreen> createState() => _WalkInRegistrationScreenState();
}

class _WalkInRegistrationScreenState extends State<WalkInRegistrationScreen> {
  final AppointmentService _appointmentService = AppointmentService();
  final _formKey = GlobalKey<FormState>();
  
  // Form controllers
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _addressController = TextEditingController();
  
  // Form fields
  String? _selectedGender;
  String? _selectedBloodGroup;
  DateTime? _dateOfBirth;
  Doctor? _selectedDoctor;
  
  // State
  List<Doctor> _doctors = [];
  bool _isLoadingDoctors = true;
  bool _isSubmitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadDoctors();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _addressController.dispose();
    super.dispose();
  }

  /// Load available doctors
  Future<void> _loadDoctors() async {
    setState(() {
      _isLoadingDoctors = true;
      _error = null;
    });

    try {
      final doctors = await _appointmentService.getAvailableDoctors();
      setState(() {
        _doctors = doctors;
        _isLoadingDoctors = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoadingDoctors = false;
      });
    }
  }

  /// Submit walk-in registration
  Future<void> _submitRegistration() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    if (_selectedDoctor == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a doctor'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    setState(() {
      _isSubmitting = true;
      _error = null;
    });

    try {
      final appointment = await _appointmentService.registerWalkIn(
        doctorId: _selectedDoctor!.id,
        patientName: _nameController.text.trim(),
        patientEmail: _emailController.text.trim().isNotEmpty 
            ? _emailController.text.trim() 
            : null,
        patientPhone: _phoneController.text.trim().isNotEmpty 
            ? _phoneController.text.trim() 
            : null,
        dateOfBirth: _dateOfBirth,
        gender: _selectedGender,
        address: _addressController.text.trim().isNotEmpty 
            ? _addressController.text.trim() 
            : null,
        bloodGroup: _selectedBloodGroup,
      );

      if (mounted) {
        // Show success dialog with queue information
        _showSuccessDialog(appointment);
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isSubmitting = false;
      });
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Registration failed: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  /// Show success dialog with queue information
  void _showSuccessDialog(Appointment appointment) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.check_circle, color: Colors.green[600], size: 32),
            const SizedBox(width: 12),
            const Text('Registration Successful'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Patient: ${_nameController.text}',
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Doctor: Dr. ${appointment.doctorName ?? _selectedDoctor?.name ?? 'Unknown'}',
              style: const TextStyle(fontSize: 14),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue[50],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.blue[200]!),
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Queue Position:',
                        style: TextStyle(fontWeight: FontWeight.w500),
                      ),
                      Text(
                        '${appointment.queuePosition ?? 'N/A'}',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.blue[700],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Estimated Wait:',
                        style: TextStyle(fontWeight: FontWeight.w500),
                      ),
                      Text(
                        '~${_calculateWaitTime(appointment)} min',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.blue[700],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop(); // Close dialog
              Navigator.of(context).pop(); // Return to nurse home
            },
            child: const Text('Done'),
          ),
        ],
      ),
    );
  }

  /// Calculate estimated wait time
  int _calculateWaitTime(Appointment appointment) {
    if (appointment.queuePosition == null || _selectedDoctor == null) {
      return 0;
    }
    return (appointment.queuePosition! - 1) * _selectedDoctor!.averageConsultationDuration;
  }

  /// Select date of birth
  Future<void> _selectDateOfBirth() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _dateOfBirth ?? DateTime(now.year - 30),
      firstDate: DateTime(1900),
      lastDate: now,
    );

    if (picked != null) {
      setState(() {
        _dateOfBirth = picked;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Walk-in Registration'),
      ),
      body: _isLoadingDoctors
          ? const LoadingIndicator(message: 'Loading doctors...')
          : _error != null && _doctors.isEmpty
              ? ErrorMessage(message: _error!, onRetry: _loadDoctors)
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16.0),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        _buildSectionHeader('Patient Information'),
                        const SizedBox(height: 16),
                        _buildNameField(),
                        const SizedBox(height: 16),
                        _buildEmailField(),
                        const SizedBox(height: 16),
                        _buildPhoneField(),
                        const SizedBox(height: 16),
                        _buildDateOfBirthField(),
                        const SizedBox(height: 16),
                        _buildGenderField(),
                        const SizedBox(height: 16),
                        _buildBloodGroupField(),
                        const SizedBox(height: 16),
                        _buildAddressField(),
                        const SizedBox(height: 24),
                        _buildSectionHeader('Doctor Selection'),
                        const SizedBox(height: 16),
                        _buildDoctorSelection(),
                        const SizedBox(height: 32),
                        _buildSubmitButton(),
                      ],
                    ),
                  ),
                ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.bold,
      ),
    );
  }

  Widget _buildNameField() {
    return TextFormField(
      controller: _nameController,
      decoration: const InputDecoration(
        labelText: 'Full Name *',
        border: OutlineInputBorder(),
        prefixIcon: Icon(Icons.person),
      ),
      validator: (value) {
        if (value == null || value.trim().isEmpty) {
          return 'Please enter patient name';
        }
        return null;
      },
    );
  }

  Widget _buildEmailField() {
    return TextFormField(
      controller: _emailController,
      decoration: const InputDecoration(
        labelText: 'Email (Optional)',
        border: OutlineInputBorder(),
        prefixIcon: Icon(Icons.email),
      ),
      keyboardType: TextInputType.emailAddress,
      validator: (value) {
        if (value != null && value.isNotEmpty) {
          final emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
          if (!emailRegex.hasMatch(value)) {
            return 'Please enter a valid email';
          }
        }
        return null;
      },
    );
  }

  Widget _buildPhoneField() {
    return TextFormField(
      controller: _phoneController,
      decoration: const InputDecoration(
        labelText: 'Phone Number (Optional)',
        border: OutlineInputBorder(),
        prefixIcon: Icon(Icons.phone),
      ),
      keyboardType: TextInputType.phone,
    );
  }

  Widget _buildDateOfBirthField() {
    return InkWell(
      onTap: _selectDateOfBirth,
      child: InputDecorator(
        decoration: const InputDecoration(
          labelText: 'Date of Birth (Optional)',
          border: OutlineInputBorder(),
          prefixIcon: Icon(Icons.calendar_today),
        ),
        child: Text(
          _dateOfBirth != null
              ? DateFormatter.formatDate(_dateOfBirth!)
              : 'Select date',
          style: TextStyle(
            color: _dateOfBirth != null ? Colors.black : Colors.grey[600],
          ),
        ),
      ),
    );
  }

  Widget _buildGenderField() {
    return DropdownButtonFormField<String>(
      decoration: const InputDecoration(
        labelText: 'Gender (Optional)',
        border: OutlineInputBorder(),
        prefixIcon: Icon(Icons.wc),
      ),
      items: ['Male', 'Female', 'Other'].map((gender) {
        return DropdownMenuItem(
          value: gender,
          child: Text(gender),
        );
      }).toList(),
      onChanged: (value) {
        setState(() {
          _selectedGender = value;
        });
      },
    );
  }

  Widget _buildBloodGroupField() {
    return DropdownButtonFormField<String>(
      decoration: const InputDecoration(
        labelText: 'Blood Group (Optional)',
        border: OutlineInputBorder(),
        prefixIcon: Icon(Icons.bloodtype),
      ),
      items: ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map((group) {
        return DropdownMenuItem(
          value: group,
          child: Text(group),
        );
      }).toList(),
      onChanged: (value) {
        setState(() {
          _selectedBloodGroup = value;
        });
      },
    );
  }

  Widget _buildAddressField() {
    return TextFormField(
      controller: _addressController,
      decoration: const InputDecoration(
        labelText: 'Address (Optional)',
        border: OutlineInputBorder(),
        prefixIcon: Icon(Icons.home),
      ),
      maxLines: 2,
    );
  }

  Widget _buildDoctorSelection() {
    if (_doctors.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Text(
            'No doctors available',
            style: TextStyle(color: Colors.grey[600]),
          ),
        ),
      );
    }

    return Column(
      children: _doctors.map((doctor) {
        final isSelected = _selectedDoctor?.id == doctor.id;
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          color: isSelected ? Colors.blue[50] : null,
          child: InkWell(
            onTap: () {
              setState(() {
                _selectedDoctor = doctor;
              });
            },
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Row(
                children: [
                  Radio<int>(
                    value: doctor.id,
                    groupValue: _selectedDoctor?.id,
                    onChanged: (value) {
                      setState(() {
                        _selectedDoctor = doctor;
                      });
                    },
                    toggleable: true,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Dr. ${doctor.name}',
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          doctor.specialization,
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.grey[600],
                          ),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          'Avg. consultation: ${doctor.averageConsultationDuration} min',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[500],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildSubmitButton() {
    return ElevatedButton(
      onPressed: _isSubmitting ? null : _submitRegistration,
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 16),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
      ),
      child: _isSubmitting
          ? const SizedBox(
              height: 20,
              width: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
              ),
            )
          : const Text(
              'Register Walk-in Patient',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
    );
  }
}
