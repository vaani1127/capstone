import 'package:flutter/material.dart';
import '../../models/doctor.dart';
import '../../models/appointment.dart';
import '../../services/appointment_service.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';
import '../../utils/date_formatter.dart';

/// Screen for booking appointments with doctors
class AppointmentBookingScreen extends StatefulWidget {
  const AppointmentBookingScreen({super.key});

  @override
  State<AppointmentBookingScreen> createState() => _AppointmentBookingScreenState();
}

class _AppointmentBookingScreenState extends State<AppointmentBookingScreen> {
  final AppointmentService _appointmentService = AppointmentService();
  
  List<Doctor> _doctors = [];
  bool _isLoading = true;
  String? _error;
  
  Doctor? _selectedDoctor;
  DateTime? _selectedDate;
  TimeOfDay? _selectedTime;
  bool _isBooking = false;

  @override
  void initState() {
    super.initState();
    _loadDoctors();
  }

  /// Load available doctors from API
  Future<void> _loadDoctors() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final doctors = await _appointmentService.getAvailableDoctors();
      setState(() {
        _doctors = doctors;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  /// Select a doctor
  void _selectDoctor(Doctor doctor) {
    setState(() {
      _selectedDoctor = doctor;
      // Reset date and time when doctor changes
      _selectedDate = null;
      _selectedTime = null;
    });
  }

  /// Select appointment date
  Future<void> _selectDate() async {
    final now = DateTime.now();
    final firstDate = now;
    final lastDate = now.add(const Duration(days: 30));

    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate ?? now,
      firstDate: firstDate,
      lastDate: lastDate,
    );

    if (picked != null) {
      setState(() {
        _selectedDate = picked;
        // Reset time when date changes
        _selectedTime = null;
      });
    }
  }

  /// Select appointment time
  Future<void> _selectTime() async {
    if (_selectedDate == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select a date first'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    final now = DateTime.now();
    final initialTime = TimeOfDay(hour: 9, minute: 0);

    final picked = await showTimePicker(
      context: context,
      initialTime: _selectedTime ?? initialTime,
    );

    if (picked != null) {
      // Validate time is in the future
      final selectedDateTime = DateTime(
        _selectedDate!.year,
        _selectedDate!.month,
        _selectedDate!.day,
        picked.hour,
        picked.minute,
      );

      if (selectedDateTime.isBefore(now)) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Please select a future time'),
              backgroundColor: Colors.red,
            ),
          );
        }
        return;
      }

      setState(() {
        _selectedTime = picked;
      });
    }
  }

  /// Book the appointment
  Future<void> _bookAppointment() async {
    if (_selectedDoctor == null || _selectedDate == null || _selectedTime == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select doctor, date, and time'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    setState(() {
      _isBooking = true;
    });

    try {
      final scheduledTime = DateTime(
        _selectedDate!.year,
        _selectedDate!.month,
        _selectedDate!.day,
        _selectedTime!.hour,
        _selectedTime!.minute,
      );

      final appointment = await _appointmentService.bookAppointment(
        doctorId: _selectedDoctor!.id,
        scheduledTime: scheduledTime,
      );

      if (mounted) {
        // Show success dialog
        await showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) => AlertDialog(
            title: Row(
              children: [
                Icon(
                  Icons.check_circle,
                  color: Colors.green,
                  size: 32,
                ),
                const SizedBox(width: 12),
                const Text('Booking Confirmed'),
              ],
            ),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Your appointment has been successfully booked!',
                  style: TextStyle(fontSize: 16),
                ),
                const SizedBox(height: 16),
                _buildConfirmationDetail('Doctor', _selectedDoctor!.name),
                _buildConfirmationDetail('Specialization', _selectedDoctor!.specialization),
                _buildConfirmationDetail('Date', DateFormatter.formatDate(scheduledTime)),
                _buildConfirmationDetail('Time', DateFormatter.formatTime(scheduledTime)),
                if (appointment.queuePosition != null)
                  _buildConfirmationDetail('Queue Position', '${appointment.queuePosition}'),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.of(context).pop();
                  Navigator.of(context).pop(); // Return to home screen
                },
                child: const Text('OK'),
              ),
            ],
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isBooking = false;
        });
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to book appointment: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Widget _buildConfirmationDetail(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 14,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontSize: 14),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Book Appointment'),
      ),
      body: _buildBody(),
      bottomNavigationBar: _buildBottomBar(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading doctors...');
    }

    if (_error != null) {
      return ErrorMessage(
        message: _error!,
        onRetry: _loadDoctors,
      );
    }

    if (_doctors.isEmpty) {
      return const Center(
        child: Text('No doctors available'),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle('Select Doctor'),
          const SizedBox(height: 12),
          _buildDoctorsList(),
          const SizedBox(height: 24),
          if (_selectedDoctor != null) ...[
            _buildSectionTitle('Select Date & Time'),
            const SizedBox(height: 12),
            _buildDateTimeSelection(),
            const SizedBox(height: 24),
            _buildBookingSummary(),
          ],
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.bold,
      ),
    );
  }

  Widget _buildDoctorsList() {
    return Column(
      children: _doctors.map((doctor) => _buildDoctorCard(doctor)).toList(),
    );
  }

  Widget _buildDoctorCard(Doctor doctor) {
    final isSelected = _selectedDoctor?.id == doctor.id;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: isSelected ? 4 : 1,
      color: isSelected ? Colors.blue[50] : null,
      child: InkWell(
        onTap: () => _selectDoctor(doctor),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            children: [
              CircleAvatar(
                radius: 30,
                backgroundColor: isSelected ? Colors.blue : Colors.grey[300],
                child: Icon(
                  Icons.person,
                  size: 32,
                  color: isSelected ? Colors.white : Colors.grey[600],
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      doctor.name,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: isSelected ? Colors.blue[900] : null,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(
                          Icons.medical_services,
                          size: 14,
                          color: Colors.grey[600],
                        ),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            doctor.specialization,
                            style: TextStyle(
                              fontSize: 14,
                              color: Colors.grey[600],
                            ),
                          ),
                        ),
                      ],
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
                          'Avg. ${doctor.averageConsultationDuration} min',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey[600],
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              if (isSelected)
                Icon(
                  Icons.check_circle,
                  color: Colors.blue,
                  size: 28,
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDateTimeSelection() {
    return Column(
      children: [
        Card(
          child: ListTile(
            leading: Icon(
              Icons.calendar_today,
              color: Theme.of(context).colorScheme.primary,
            ),
            title: const Text('Date'),
            subtitle: Text(
              _selectedDate != null
                  ? DateFormatter.formatDate(_selectedDate!)
                  : 'Select date',
            ),
            trailing: const Icon(Icons.arrow_forward_ios, size: 16),
            onTap: _selectDate,
          ),
        ),
        const SizedBox(height: 12),
        Card(
          child: ListTile(
            leading: Icon(
              Icons.access_time,
              color: Theme.of(context).colorScheme.primary,
            ),
            title: const Text('Time'),
            subtitle: Text(
              _selectedTime != null
                  ? _selectedTime!.format(context)
                  : 'Select time',
            ),
            trailing: const Icon(Icons.arrow_forward_ios, size: 16),
            onTap: _selectTime,
          ),
        ),
      ],
    );
  }

  Widget _buildBookingSummary() {
    if (_selectedDoctor == null || _selectedDate == null || _selectedTime == null) {
      return const SizedBox.shrink();
    }

    return Card(
      color: Colors.blue[50],
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.info_outline,
                  color: Colors.blue[700],
                  size: 20,
                ),
                const SizedBox(width: 8),
                Text(
                  'Booking Summary',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Colors.blue[900],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            _buildSummaryRow('Doctor', _selectedDoctor!.name),
            _buildSummaryRow('Specialization', _selectedDoctor!.specialization),
            _buildSummaryRow('Date', DateFormatter.formatDate(_selectedDate!)),
            _buildSummaryRow('Time', _selectedTime!.format(context)),
            _buildSummaryRow(
              'Est. Duration',
              '${_selectedDoctor!.averageConsultationDuration} minutes',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(
              '$label:',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[700],
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomBar() {
    if (_selectedDoctor == null || _selectedDate == null || _selectedTime == null) {
      return const SizedBox.shrink();
    }

    return Container(
      padding: const EdgeInsets.all(16.0),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withOpacity(0.3),
            spreadRadius: 1,
            blurRadius: 5,
            offset: const Offset(0, -3),
          ),
        ],
      ),
      child: SafeArea(
        child: ElevatedButton(
          onPressed: _isBooking ? null : _bookAppointment,
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
            minimumSize: const Size(double.infinity, 50),
          ),
          child: _isBooking
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                )
              : const Text(
                  'Confirm Booking',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
        ),
      ),
    );
  }
}
