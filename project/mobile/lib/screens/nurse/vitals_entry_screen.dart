import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../services/vitals_service.dart';
import '../../widgets/loading_indicator.dart';

/// Form screen for a Nurse (or Doctor) to record patient vital signs.
///
/// [patientId] is provided as a route argument by the caller:
///   Navigator.of(context).pushNamed('/vitals/entry',
///     arguments: {'patientId': someId});
///
/// BMI is computed live as the user types weight and height.
class VitalsEntryScreen extends StatefulWidget {
  final int? patientId;

  const VitalsEntryScreen({super.key, this.patientId});

  @override
  State<VitalsEntryScreen> createState() => _VitalsEntryScreenState();
}

class _VitalsEntryScreenState extends State<VitalsEntryScreen> {
  final _formKey = GlobalKey<FormState>();
  final VitalsService _vitalsService = VitalsService();

  // Controllers
  final _systolicController = TextEditingController();
  final _diastolicController = TextEditingController();
  final _heartRateController = TextEditingController();
  final _temperatureController = TextEditingController();
  final _respiratoryRateController = TextEditingController();
  final _spo2Controller = TextEditingController();
  final _weightController = TextEditingController();
  final _heightController = TextEditingController();
  final _notesController = TextEditingController();

  double? _computedBmi;
  bool _isSubmitting = false;

  @override
  void initState() {
    super.initState();
    _weightController.addListener(_updateBmi);
    _heightController.addListener(_updateBmi);
  }

  @override
  void dispose() {
    _systolicController.dispose();
    _diastolicController.dispose();
    _heartRateController.dispose();
    _temperatureController.dispose();
    _respiratoryRateController.dispose();
    _spo2Controller.dispose();
    _weightController.dispose();
    _heightController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  // ---------------------------------------------------------------------------
  // BMI
  // ---------------------------------------------------------------------------

  void _updateBmi() {
    final weight = double.tryParse(_weightController.text);
    final height = double.tryParse(_heightController.text);
    setState(() {
      if (weight != null && height != null && height > 0) {
        final hm = height / 100.0;
        _computedBmi = double.parse((weight / (hm * hm)).toStringAsFixed(1));
      } else {
        _computedBmi = null;
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Submit
  // ---------------------------------------------------------------------------

  Future<void> _submit() async {
    if (widget.patientId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No patient selected. Please go back and select a patient.'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    if (!_formKey.currentState!.validate()) return;

    setState(() => _isSubmitting = true);

    try {
      await _vitalsService.recordVitals(
        patientId: widget.patientId!,
        systolicBp: int.tryParse(_systolicController.text),
        diastolicBp: int.tryParse(_diastolicController.text),
        heartRate: int.tryParse(_heartRateController.text),
        temperature: double.tryParse(_temperatureController.text),
        respiratoryRate: int.tryParse(_respiratoryRateController.text),
        oxygenSaturation: double.tryParse(_spo2Controller.text),
        weightKg: double.tryParse(_weightController.text),
        heightCm: double.tryParse(_heightController.text),
        notes: _notesController.text.trim().isEmpty
            ? null
            : _notesController.text.trim(),
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Vitals recorded successfully'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.of(context).pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to record vitals: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  // ---------------------------------------------------------------------------
  // Validators
  // ---------------------------------------------------------------------------

  String? _validateOptionalInt(String? v, int min, int max, String label) {
    if (v == null || v.trim().isEmpty) return null;
    final n = int.tryParse(v.trim());
    if (n == null) return '$label must be a whole number';
    if (n < min || n > max) return '$label must be between $min and $max';
    return null;
  }

  String? _validateOptionalDouble(String? v, double min, double max, String label) {
    if (v == null || v.trim().isEmpty) return null;
    final n = double.tryParse(v.trim());
    if (n == null) return '$label must be a number';
    if (n < min || n > max) return '$label must be between $min and $max';
    return null;
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.patientId != null
              ? 'Record Vitals (Patient #${widget.patientId})'
              : 'Record Vitals',
        ),
      ),
      body: _isSubmitting
          ? const LoadingIndicator(message: 'Saving vitals...')
          : Form(
              key: _formKey,
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildSectionHeader('Blood Pressure', Icons.favorite),
                    _buildRow(
                      _buildIntField(
                        controller: _systolicController,
                        label: 'Systolic (mmHg)',
                        min: 0, max: 300,
                        hint: 'e.g. 120',
                      ),
                      _buildIntField(
                        controller: _diastolicController,
                        label: 'Diastolic (mmHg)',
                        min: 0, max: 200,
                        hint: 'e.g. 80',
                      ),
                    ),
                    const SizedBox(height: 16),
                    _buildSectionHeader('Cardiovascular', Icons.monitor_heart),
                    _buildIntField(
                      controller: _heartRateController,
                      label: 'Heart Rate (bpm)',
                      min: 0, max: 300,
                      hint: 'e.g. 72',
                    ),
                    const SizedBox(height: 16),
                    _buildSectionHeader('Respiratory', Icons.air),
                    _buildRow(
                      _buildIntField(
                        controller: _respiratoryRateController,
                        label: 'Respiratory Rate (br/min)',
                        min: 0, max: 100,
                        hint: 'e.g. 16',
                      ),
                      _buildDoubleField(
                        controller: _spo2Controller,
                        label: 'SpO2 (%)',
                        min: 0, max: 100,
                        hint: 'e.g. 98',
                      ),
                    ),
                    const SizedBox(height: 16),
                    _buildSectionHeader('Temperature', Icons.thermostat),
                    _buildDoubleField(
                      controller: _temperatureController,
                      label: 'Temperature (°F)',
                      min: 86, max: 113,
                      hint: 'e.g. 98.6',
                    ),
                    const SizedBox(height: 16),
                    _buildSectionHeader('Anthropometrics', Icons.monitor_weight),
                    _buildRow(
                      _buildDoubleField(
                        controller: _weightController,
                        label: 'Weight (kg)',
                        min: 0, max: 700,
                        hint: 'e.g. 70.5',
                      ),
                      _buildDoubleField(
                        controller: _heightController,
                        label: 'Height (cm)',
                        min: 0, max: 300,
                        hint: 'e.g. 175',
                      ),
                    ),
                    if (_computedBmi != null) ...[
                      const SizedBox(height: 8),
                      _buildBmiDisplay(_computedBmi!),
                    ],
                    const SizedBox(height: 16),
                    _buildSectionHeader('Notes', Icons.notes),
                    TextFormField(
                      controller: _notesController,
                      maxLines: 3,
                      decoration: const InputDecoration(
                        labelText: 'Clinical notes (optional)',
                        border: OutlineInputBorder(),
                        alignLabelWithHint: true,
                      ),
                    ),
                    const SizedBox(height: 32),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: _submit,
                        icon: const Icon(Icons.save),
                        label: const Text('Save Vitals'),
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 14),
                          backgroundColor: Theme.of(context).colorScheme.primary,
                          foregroundColor: Colors.white,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }

  Widget _buildSectionHeader(String title, IconData icon) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          Icon(icon, size: 18, color: Theme.of(context).colorScheme.primary),
          const SizedBox(width: 6),
          Text(
            title,
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w600,
              color: Theme.of(context).colorScheme.primary,
            ),
          ),
          const SizedBox(width: 8),
          const Expanded(child: Divider()),
        ],
      ),
    );
  }

  Widget _buildRow(Widget left, Widget right) {
    return Row(
      children: [
        Expanded(child: left),
        const SizedBox(width: 12),
        Expanded(child: right),
      ],
    );
  }

  Widget _buildIntField({
    required TextEditingController controller,
    required String label,
    required int min,
    required int max,
    required String hint,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: TextInputType.number,
      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        border: const OutlineInputBorder(),
      ),
      validator: (v) => _validateOptionalInt(v, min, max, label),
    );
  }

  Widget _buildDoubleField({
    required TextEditingController controller,
    required String label,
    required double min,
    required double max,
    required String hint,
  }) {
    return TextFormField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      inputFormatters: [
        FilteringTextInputFormatter.allow(RegExp(r'^\d*\.?\d*')),
      ],
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        border: const OutlineInputBorder(),
      ),
      validator: (v) => _validateOptionalDouble(v, min, max, label),
    );
  }

  Widget _buildBmiDisplay(double bmi) {
    Color color;
    String category;
    if (bmi < 18.5) {
      color = Colors.blue;
      category = 'Underweight';
    } else if (bmi < 25) {
      color = Colors.green;
      category = 'Normal';
    } else if (bmi < 30) {
      color = Colors.orange;
      category = 'Overweight';
    } else {
      color = Colors.red;
      category = 'Obese';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.4)),
      ),
      child: Row(
        children: [
          Icon(Icons.calculate, size: 16, color: color),
          const SizedBox(width: 8),
          Text(
            'BMI: ${bmi.toStringAsFixed(1)}',
            style: TextStyle(fontWeight: FontWeight.w600, color: color),
          ),
          const SizedBox(width: 8),
          Text(
            '($category)',
            style: TextStyle(fontSize: 13, color: color),
          ),
        ],
      ),
    );
  }
}
