import 'package:flutter/material.dart';
import '../../models/organization.dart';
import '../../services/organization_service.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';

/// Paginated list of healthcare organisations for admin review.
///
/// Tapping a row opens a detail bottom sheet with all fields.
class OrganizationsScreen extends StatefulWidget {
  const OrganizationsScreen({super.key});

  @override
  State<OrganizationsScreen> createState() => _OrganizationsScreenState();
}

class _OrganizationsScreenState extends State<OrganizationsScreen> {
  final OrganizationService _service = OrganizationService();

  final List<Organization> _items = [];
  int _total = 0;
  int _currentPage = 1;
  static const int _pageSize = 20;

  bool _isLoading = true;
  bool _isLoadingMore = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadPage(1, replace: true);
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
      final result =
          await _service.getOrganizations(page: page, pageSize: _pageSize);
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

  void _showDetail(Organization org) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => DraggableScrollableSheet(
        expand: false,
        initialChildSize: 0.55,
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
              Text(org.name,
                  style: const TextStyle(
                      fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              _detailRow('Address', org.address),
              _detailRow('City', org.city),
              _detailRow('State', org.state),
              _detailRow('ZIP', org.zip),
              _detailRow('Phone', org.phone),
              _detailRow('Revenue',
                  org.revenue != null ? '\$${org.revenue!.toStringAsFixed(2)}' : null),
              _detailRow('Utilization', org.utilizationLabel),
              if (org.lat != null && org.lon != null)
                _detailRow('Coordinates',
                    '${org.lat!.toStringAsFixed(5)}, ${org.lon!.toStringAsFixed(5)}'),
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
        title: Text(_total > 0 ? 'Organizations ($_total)' : 'Organizations'),
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading organizations...');
    }
    if (_error != null) {
      return ErrorMessage(
          message: _error!, onRetry: () => _loadPage(1, replace: true));
    }
    if (_items.isEmpty) {
      return const Center(child: Text('No organizations found.'));
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
        final org = _items[i];
        return Card(
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: ListTile(
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            leading: CircleAvatar(
              backgroundColor: Colors.teal.withOpacity(0.12),
              child: const Icon(Icons.business, color: Colors.teal),
            ),
            title: Text(org.name,
                style: const TextStyle(fontWeight: FontWeight.w600)),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(org.location,
                    style: TextStyle(fontSize: 13, color: Colors.grey[600])),
                if (org.utilization != null)
                  Text('Utilization: ${org.utilizationLabel}',
                      style: TextStyle(fontSize: 12, color: Colors.grey[500])),
              ],
            ),
            isThreeLine: org.utilization != null,
            trailing: const Icon(Icons.chevron_right, color: Colors.grey),
            onTap: () => _showDetail(org),
          ),
        );
      },
    );
  }
}
