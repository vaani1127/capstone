import 'package:flutter/material.dart';
import '../../models/allergy.dart';
import '../../services/allergy_service.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';

/// Screen for viewing and managing a patient's allergy records.
///
/// Navigate to this screen via:
///   Navigator.of(context).pushNamed('/allergies', arguments: {
///     'patientId':   someId,
///     'patientName': 'Jane Doe',   // optional
///   });
///
/// Doctors can:
///   - View all active allergies with severity colour coding
///   - Add a new allergy via the FAB (opens a bottom sheet form)
///   - Deactivate an allergy by swiping left or tapping the deactivate button
class AllergiesScreen extends StatefulWidget {
  final int patientId;
  final String? patientName;

  const AllergiesScreen({
    super.key,
    required this.patientId,
    this.patientName,
  });

  @override
  State<AllergiesScreen> createState() => _AllergiesScreenState();
}

class _AllergiesScreenState extends State<AllergiesScreen> {
  final AllergyService _service = AllergyService();

  List<Allergy> _allergies = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final rows = await _service.getPatientAllergies(widget.patientId);
      setState(() {
        _allergies = rows;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  // ---------------------------------------------------------------------------
  // Deactivation
  // ---------------------------------------------------------------------------

  Future<bool> _confirmAndDeactivate(Allergy allergy) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Deactivate Allergy'),
        content: Text(
          'Mark "${allergy.allergen}" as no longer active?\n\n'
          'The record is preserved for clinical history.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('Deactivate', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );

    if (confirmed != true) return false;

    try {
      await _service.deactivateAllergy(allergy.id);
      if (mounted) {
        setState(() => _allergies.removeWhere((a) => a.id == allergy.id));
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${allergy.allergen} marked as inactive'),
            backgroundColor: Colors.green,
          ),
        );
      }
      return true;
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to deactivate: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
      return false;
    }
  }

  // ---------------------------------------------------------------------------
  // Add allergy bottom sheet
  // ---------------------------------------------------------------------------

  Future<void> _showAddSheet() async {
    final allergenCtrl = TextEditingController();
    final reactionCtrl = TextEditingController();
    final notesCtrl = TextEditingController();
    String selectedSeverity = 'mild';
    DateTime? onsetDate;
    bool isSaving = false;
    final formKey = GlobalKey<FormState>();

    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setSheet) => Padding(
          padding: EdgeInsets.only(
            left: 16,
            right: 16,
            top: 20,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 24,
          ),
          child: Form(
            key: formKey,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Header
                  Row(
                    children: [
                      const Icon(Icons.add_circle_outline, color: Colors.red),
                      const SizedBox(width: 8),
                      Text(
                        'Add Allergy',
                        style: Theme.of(ctx)
                            .textTheme
                            .titleLarge
                            ?.copyWith(fontWeight: FontWeight.bold),
                      ),
                      const Spacer(),
                      IconButton(
                        icon: const Icon(Icons.close),
                        onPressed: () => Navigator.of(ctx).pop(),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  // Allergen
                  TextFormField(
                    controller: allergenCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Allergen *',
                      hintText: 'e.g., Penicillin, Peanuts, Latex',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.warning_amber_rounded),
                    ),
                    textCapitalization: TextCapitalization.sentences,
                    validator: (v) =>
                        (v == null || v.trim().isEmpty) ? 'Allergen is required' : null,
                  ),
                  const SizedBox(height: 12),

                  // Reaction
                  TextFormField(
                    controller: reactionCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Reaction (optional)',
                      hintText: 'e.g., Anaphylaxis, Hives, Rash',
                      border: OutlineInputBorder(),
                    ),
                    maxLines: 2,
                  ),
                  const SizedBox(height: 12),

                  // Severity
                  DropdownButtonFormField<String>(
                    value: selectedSeverity,
                    decoration: const InputDecoration(
                      labelText: 'Severity *',
                      border: OutlineInputBorder(),
                    ),
                    items: [
                      _severityItem('mild', Colors.amber),
                      _severityItem('moderate', Colors.orange),
                      _severityItem('severe', Colors.red),
                    ],
                    onChanged: (v) =>
                        setSheet(() => selectedSeverity = v ?? 'mild'),
                    validator: (v) =>
                        v == null ? 'Please select a severity' : null,
                  ),
                  const SizedBox(height: 12),

                  // Onset date
                  GestureDetector(
                    onTap: () async {
                      final picked = await showDatePicker(
                        context: ctx,
                        initialDate: onsetDate ?? DateTime.now(),
                        firstDate: DateTime(1900),
                        lastDate: DateTime.now(),
                      );
                      if (picked != null) {
                        setSheet(() => onsetDate = picked);
                      }
                    },
                    child: InputDecorator(
                      decoration: const InputDecoration(
                        labelText: 'Onset Date (optional)',
                        border: OutlineInputBorder(),
                        suffixIcon: Icon(Icons.calendar_today),
                      ),
                      child: Text(
                        onsetDate != null
                            ? DateFormatter.formatDate(onsetDate!)
                            : 'Tap to select date',
                        style: TextStyle(
                          color: onsetDate != null
                              ? Colors.black87
                              : Colors.grey[600],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),

                  // Notes
                  TextFormField(
                    controller: notesCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Notes (optional)',
                      border: OutlineInputBorder(),
                      alignLabelWithHint: true,
                    ),
                    maxLines: 2,
                  ),
                  const SizedBox(height: 20),

                  // Save button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: isSaving
                          ? null
                          : () async {
                              if (!formKey.currentState!.validate()) return;
                              setSheet(() => isSaving = true);
                              try {
                                final allergy = await _service.recordAllergy(
                                  patientId: widget.patientId,
                                  allergen: allergenCtrl.text.trim(),
                                  reaction: reactionCtrl.text.trim().isEmpty
                                      ? null
                                      : reactionCtrl.text.trim(),
                                  severity: selectedSeverity,
                                  onsetDate: onsetDate,
                                  notes: notesCtrl.text.trim().isEmpty
                                      ? null
                                      : notesCtrl.text.trim(),
                                );
                                if (mounted) {
                                  Navigator.of(ctx).pop();
                                  setState(() => _allergies.insert(0, allergy));
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text('Allergy recorded'),
                                      backgroundColor: Colors.green,
                                    ),
                                  );
                                }
                              } catch (e) {
                                setSheet(() => isSaving = false);
                                if (mounted) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(
                                      content: Text('Failed to save: $e'),
                                      backgroundColor: Colors.red,
                                    ),
                                  );
                                }
                              }
                            },
                      icon: isSaving
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2, color: Colors.white),
                            )
                          : const Icon(Icons.save),
                      label: Text(isSaving ? 'Saving...' : 'Save Allergy'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        backgroundColor: Colors.red,
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  DropdownMenuItem<String> _severityItem(String value, Color color) {
    return DropdownMenuItem(
      value: value,
      child: Row(
        children: [
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 8),
          Text(value[0].toUpperCase() + value.substring(1)),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    final title = widget.patientName != null
        ? '${widget.patientName}\'s Allergies'
        : 'Allergies';

    return Scaffold(
      appBar: AppBar(
        title: Text(title),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: _load,
          ),
        ],
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showAddSheet,
        icon: const Icon(Icons.add),
        label: const Text('Add Allergy'),
        backgroundColor: Colors.red,
        foregroundColor: Colors.white,
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading allergy records...');
    }
    if (_error != null) {
      return ErrorMessage(message: _error!, onRetry: _load);
    }
    if (_allergies.isEmpty) {
      return _buildEmpty();
    }
    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
      itemCount: _allergies.length,
      itemBuilder: (_, i) => _buildAllergyCard(_allergies[i]),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.check_circle_outline, size: 80, color: Colors.green[400]),
          const SizedBox(height: 16),
          const Text(
            'No known allergies',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          Text(
            'Tap the button below to record an allergy.',
            style: TextStyle(fontSize: 14, color: Colors.grey[600]),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Allergy card
  // ---------------------------------------------------------------------------

  Widget _buildAllergyCard(Allergy allergy) {
    final color = allergy.severityColor;

    return Dismissible(
      key: Key('allergy_${allergy.id}'),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        decoration: BoxDecoration(
          color: Colors.red.shade100,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.do_not_disturb_on, color: Colors.red.shade700, size: 28),
            const SizedBox(height: 4),
            Text(
              'Deactivate',
              style: TextStyle(
                color: Colors.red.shade700,
                fontSize: 11,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
      confirmDismiss: (_) => _confirmAndDeactivate(allergy),
      child: Card(
        margin: const EdgeInsets.only(bottom: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        clipBehavior: Clip.antiAlias,
        child: IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Severity colour bar
              Container(width: 6, color: color),
              // Content
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Header row
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            child: Text(
                              allergy.allergen,
                              style: const TextStyle(
                                fontSize: 17,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          _buildSeverityChip(allergy),
                        ],
                      ),
                      // Reaction
                      if (allergy.reaction != null &&
                          allergy.reaction!.isNotEmpty) ...[
                        const SizedBox(height: 6),
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(Icons.bolt, size: 14, color: Colors.grey[600]),
                            const SizedBox(width: 4),
                            Expanded(
                              child: Text(
                                allergy.reaction!,
                                style: TextStyle(
                                  fontSize: 13,
                                  color: Colors.grey[700],
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                      // Onset date
                      if (allergy.onsetDate != null) ...[
                        const SizedBox(height: 4),
                        Row(
                          children: [
                            Icon(Icons.calendar_today,
                                size: 12, color: Colors.grey[500]),
                            const SizedBox(width: 4),
                            Text(
                              'Onset: ${DateFormatter.formatDate(allergy.onsetDate!)}',
                              style: TextStyle(
                                  fontSize: 12, color: Colors.grey[600]),
                            ),
                          ],
                        ),
                      ],
                      // Notes
                      if (allergy.notes != null &&
                          allergy.notes!.isNotEmpty) ...[
                        const SizedBox(height: 4),
                        Text(
                          allergy.notes!,
                          style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey[600],
                              fontStyle: FontStyle.italic),
                        ),
                      ],
                      // Footer
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Icon(Icons.person_outline,
                              size: 12, color: Colors.grey[500]),
                          const SizedBox(width: 4),
                          Expanded(
                            child: Text(
                              allergy.recordedByName != null
                                  ? 'Recorded by ${allergy.recordedByName}'
                                  : 'Recorded ${DateFormatter.formatDate(allergy.createdAt)}',
                              style: TextStyle(
                                  fontSize: 11, color: Colors.grey[500]),
                            ),
                          ),
                          // Deactivate tap button
                          TextButton.icon(
                            onPressed: () => _confirmAndDeactivate(allergy),
                            icon: Icon(Icons.do_not_disturb_on,
                                size: 14, color: Colors.red[400]),
                            label: Text(
                              'Deactivate',
                              style: TextStyle(
                                  fontSize: 12, color: Colors.red[400]),
                            ),
                            style: TextButton.styleFrom(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 6, vertical: 0),
                              minimumSize: Size.zero,
                              tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSeverityChip(Allergy allergy) {
    final color = allergy.severityColor;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Text(
        allergy.severityLabel,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: color.withOpacity(0.9),
        ),
      ),
    );
  }
}
