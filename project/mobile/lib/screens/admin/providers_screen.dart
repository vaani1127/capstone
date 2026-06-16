import 'package:flutter/material.dart';
import '../../models/provider.dart';
import '../../services/provider_service.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';

/// Paginated list of healthcare providers for admin review.
///
/// A speciality filter dropdown is populated from GET /providers/by-speciality.
/// Tapping a row opens a detail bottom sheet with all fields.
class ProvidersScreen extends StatefulWidget {
  const ProvidersScreen({super.key});

  @override
  State<ProvidersScreen> createState() => _ProvidersScreenState();
}

class _ProvidersScreenState extends State<ProvidersScreen> {
  final ProviderService _service = ProviderService();

  final List<Provider> _items = [];
  List<String> _specialities = [];
  String? _selectedSpeciality;

  int _total = 0;
  int _currentPage = 1;
  static const int _pageSize = 20;

  bool _isLoading = true;
  bool _isLoadingMore = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    try {
      final specs = await _service.getSpecialities();
      if (mounted) setState(() => _specialities = specs);
    } catch (_) {
      // Speciality filter is optional; silently ignore errors
    }
    await _loadPage(1, replace: true);
  }

  Future<void> _loadPage(int page, {bool replace = false}) async {
    if (replace) {
      setState(() {
        _isLoading = true;
        _error = null;
      });
    } else {
      setState(() => _isLoadingMore = true);
    }

    try {
      final result = await _service.getProviders(
        speciality: _selectedSpeciality,
        page: page,
        pageSize: _pageSize,
      );
      setState(() {
        if (replace) _items.clear();
        _items.addAll(result.items);
        _total = result.total;
        _currentPage = page;
        _isLoading = false;
        _isLoadingMore = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
        _isLoadingMore = false;
      });
    }
  }

  bool get _hasMore => _currentPage * _pageSize < _total;

  void _onSpecialityChanged(String? value) {
    setState(() => _selectedSpeciality = value);
    _loadPage(1, replace: true);
  }

  void _showDetail(Provider prov) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.6,
        maxChildSize: 0.9,
        builder: (_, ctrl) => SingleChildScrollView(
          controller: ctrl,
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: Colors.grey[300],
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              Text(prov.name,
                  style: const TextStyle(
                      fontSize: 20, fontWeight: FontWeight.bold)),
              if (prov.speciality != null) ...[
                const SizedBox(height: 4),
                Text(prov.speciality!,
                    style: TextStyle(fontSize: 14, color: Colors.indigo[600])),
              ],
              const SizedBox(height: 16),
              _detailRow('Gender', prov.gender),
              _detailRow('Organisation', prov.organizationName),
              _detailRow('Address', prov.address),
              _detailRow('City', prov.city),
              _detailRow('State', prov.state),
              _detailRow('ZIP', prov.zip),
              _detailRow('Encounters', '${prov.encounterCount}'),
              _detailRow('Procedures', '${prov.procedureCount}'),
              if (prov.lat != null && prov.lon != null)
                _detailRow('Coordinates',
                    '${prov.lat!.toStringAsFixed(5)}, ${prov.lon!.toStringAsFixed(5)}'),
            ],
          ),
        ),
      ),
    );
  }

  Widget _detailRow(String label, String? value) {
    if (value == null || value.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(
              '$label:',
              style: TextStyle(
                  fontWeight: FontWeight.w500, color: Colors.grey[700]),
            ),
          ),
          Expanded(child: Text(value, style: const TextStyle(fontSize: 14))),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_total > 0 ? 'Providers ($_total)' : 'Providers'),
      ),
      body: Column(
        children: [
          _buildFilterBar(),
          Expanded(child: _buildBody()),
        ],
      ),
    );
  }

  Widget _buildFilterBar() {
    if (_specialities.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
      child: DropdownButtonFormField<String>(
        value: _selectedSpeciality,
        decoration: const InputDecoration(
          labelText: 'Filter by Speciality',
          border: OutlineInputBorder(),
          contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        ),
        items: [
          const DropdownMenuItem<String>(value: null, child: Text('All Specialities')),
          ..._specialities.map(
            (s) => DropdownMenuItem<String>(value: s, child: Text(s)),
          ),
        ],
        onChanged: _onSpecialityChanged,
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading providers...');
    }
    if (_error != null) {
      return ErrorMessage(
          message: _error!, onRetry: () => _loadPage(1, replace: true));
    }
    if (_items.isEmpty) {
      return const Center(child: Text('No providers found.'));
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: _items.length + (_hasMore ? 1 : 0),
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (_, i) {
        if (i == _items.length) {
          return Center(
            child: _isLoadingMore
                ? const CircularProgressIndicator()
                : TextButton(
                    onPressed: () => _loadPage(_currentPage + 1),
                    child: const Text('Load more'),
                  ),
          );
        }
        final prov = _items[i];
        return Card(
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: ListTile(
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            leading: CircleAvatar(
              backgroundColor: Colors.indigo.withOpacity(0.12),
              child: Text(
                prov.name.isNotEmpty ? prov.name[0].toUpperCase() : '?',
                style: const TextStyle(
                    fontWeight: FontWeight.bold, color: Colors.indigo),
              ),
            ),
            title: Text(prov.name,
                style: const TextStyle(fontWeight: FontWeight.w600)),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (prov.speciality != null)
                  Text(prov.speciality!,
                      style:
                          TextStyle(fontSize: 13, color: Colors.indigo[400])),
                Text(prov.location,
                    style: TextStyle(fontSize: 12, color: Colors.grey[600])),
              ],
            ),
            isThreeLine: prov.speciality != null,
            trailing: const Icon(Icons.chevron_right, color: Colors.grey),
            onTap: () => _showDetail(prov),
          ),
        );
      },
    );
  }
}
