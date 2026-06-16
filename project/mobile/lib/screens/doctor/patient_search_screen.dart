import 'dart:async';
import 'package:flutter/material.dart';
import '../../models/patient.dart';
import '../../services/api_client.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';
import '../patient/medical_history_screen.dart';

/// Doctor/Nurse screen for searching patients by name or phone number.
///
/// Calls GET /api/v1/patients/search?q={query} with a 400 ms debounce as the
/// user types. Tapping a result navigates to [MedicalHistoryScreen] for that
/// patient's records.
class PatientSearchScreen extends StatefulWidget {
  const PatientSearchScreen({super.key});

  @override
  State<PatientSearchScreen> createState() => _PatientSearchScreenState();
}

class _PatientSearchScreenState extends State<PatientSearchScreen> {
  final ApiClient _apiClient = ApiClient();
  final TextEditingController _searchController = TextEditingController();

  List<Patient> _results = [];
  bool _isLoading = false;
  bool _hasSearched = false;
  String? _error;
  Timer? _debounce;

  @override
  void dispose() {
    _searchController.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  // ---------------------------------------------------------------------------
  // Search logic
  // ---------------------------------------------------------------------------

  void _onSearchChanged(String query) {
    _debounce?.cancel();

    if (query.trim().isEmpty) {
      setState(() {
        _results = [];
        _hasSearched = false;
        _error = null;
        _isLoading = false;
      });
      return;
    }

    _debounce = Timer(const Duration(milliseconds: 400), () {
      _performSearch(query.trim());
    });
  }

  Future<void> _performSearch(String query) async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final response = await _apiClient.get(
        '/patients/search?q=${Uri.encodeComponent(query)}',
      );

      final raw = response['results'] as List;
      setState(() {
        _results = raw
            .map((json) => Patient.fromJson(json as Map<String, dynamic>))
            .toList();
        _hasSearched = true;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
        _hasSearched = true;
      });
    }
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Patient Search')),
      body: Column(
        children: [
          _buildSearchBar(),
          Expanded(child: _buildBody()),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      child: TextField(
        controller: _searchController,
        onChanged: _onSearchChanged,
        autofocus: true,
        textInputAction: TextInputAction.search,
        decoration: InputDecoration(
          hintText: 'Search by name or phone number…',
          prefixIcon: const Icon(Icons.search),
          suffixIcon: _searchController.text.isNotEmpty
              ? IconButton(
                  icon: const Icon(Icons.clear),
                  tooltip: 'Clear',
                  onPressed: () {
                    _searchController.clear();
                    _onSearchChanged('');
                  },
                )
              : null,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          filled: true,
          fillColor: Colors.grey[100],
          contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 16),
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Searching patients…');
    }

    if (_error != null) {
      return ErrorMessage(
        message: _error!,
        onRetry: () => _performSearch(_searchController.text.trim()),
      );
    }

    if (!_hasSearched) {
      return _buildPromptState();
    }

    if (_results.isEmpty) {
      return _buildEmptyState();
    }

    return _buildResultsList();
  }

  // ---------------------------------------------------------------------------
  // Empty / prompt states
  // ---------------------------------------------------------------------------

  Widget _buildPromptState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.person_search, size: 80, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text(
            'Search for a patient',
            style: TextStyle(fontSize: 18, color: Colors.grey[600]),
          ),
          const SizedBox(height: 8),
          Text(
            'Enter a name or phone number above',
            style: TextStyle(fontSize: 14, color: Colors.grey[500]),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.search_off, size: 80, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text(
            'No patients found',
            style: TextStyle(fontSize: 18, color: Colors.grey[600]),
          ),
          const SizedBox(height: 8),
          Text(
            'Try a different name or phone number',
            style: TextStyle(fontSize: 14, color: Colors.grey[500]),
          ),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Results list
  // ---------------------------------------------------------------------------

  Widget _buildResultsList() {
    return ListView.separated(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      itemCount: _results.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (context, index) => _buildPatientCard(_results[index]),
    );
  }

  Widget _buildPatientCard(Patient patient) {
    final age = _ageFromDob(patient.dateOfBirth);

    return Card(
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => MedicalHistoryScreen(
              patientId: patient.id,
              patientName: patient.name,
            ),
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // Avatar
              CircleAvatar(
                radius: 26,
                backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                child: Text(
                  patient.name.isNotEmpty
                      ? patient.name[0].toUpperCase()
                      : '?',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: Theme.of(context).colorScheme.onPrimaryContainer,
                  ),
                ),
              ),
              const SizedBox(width: 16),
              // Details
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      patient.name,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 12,
                      runSpacing: 4,
                      children: [
                        if (age != null)
                          _buildChip(Icons.cake_outlined, '$age yrs', Colors.blueGrey),
                        if (patient.bloodGroup != null)
                          _buildChip(Icons.water_drop_outlined, patient.bloodGroup!, Colors.red),
                        if (patient.phone != null)
                          _buildChip(Icons.phone_outlined, patient.phone!, Colors.green),
                      ],
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: Colors.grey),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildChip(IconData icon, String label, Color color) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: color.withOpacity(0.8)),
        const SizedBox(width: 3),
        Text(
          label,
          style: TextStyle(
            fontSize: 13,
            color: color.withOpacity(0.9),
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  int? _ageFromDob(DateTime? dob) {
    if (dob == null) return null;
    final today = DateTime.now();
    int age = today.year - dob.year;
    if (today.month < dob.month ||
        (today.month == dob.month && today.day < dob.day)) {
      age--;
    }
    return age;
  }
}
