import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';

import 'behavioral_score_trend_screen.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as ws_status;
import '../../config/app_config.dart';
import '../../services/api_client.dart';
import '../../utils/date_formatter.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';

/// Admin-only screen that shows ML-detected behavioural anomaly alerts
/// and connects to the admin WebSocket channel for live updates.
class AnomalyAlertsScreen extends StatefulWidget {
  const AnomalyAlertsScreen({super.key});

  @override
  State<AnomalyAlertsScreen> createState() => _AnomalyAlertsScreenState();
}

class _AnomalyAlertsScreenState extends State<AnomalyAlertsScreen> {
  final ApiClient _apiClient = ApiClient();

  List<Map<String, dynamic>> _alerts = [];
  Map<String, dynamic>? _stats;
  bool _isLoading = true;
  String? _error;

  // Per-card loading state while an acknowledge request is in flight.
  final Set<int> _acknowledgingIds = {};

  // Dedicated WebSocket channel for admin anomaly feed.
  WebSocketChannel? _wsChannel;
  StreamSubscription? _wsSubscription;

  @override
  void initState() {
    super.initState();
    _loadData();
    _connectWebSocket();
  }

  @override
  void dispose() {
    _wsSubscription?.cancel();
    _wsChannel?.sink.close(ws_status.goingAway);
    super.dispose();
  }

  // ---------------------------------------------------------------------------
  // Data loading
  // ---------------------------------------------------------------------------

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final results = await Future.wait([
        _apiClient.get('/anomaly/alerts?page=1&page_size=50'),
        _apiClient.get('/anomaly/stats'),
      ]);

      final alertsData = results[0] as Map<String, dynamic>;
      final statsData = results[1] as Map<String, dynamic>;

      setState(() {
        _alerts = List<Map<String, dynamic>>.from(
          (alertsData['alerts'] as List? ?? []).map(
            (e) => Map<String, dynamic>.from(e as Map),
          ),
        );
        _stats = statsData;
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
  // WebSocket — live alert feed
  // ---------------------------------------------------------------------------

  void _connectWebSocket() {
    final token = _apiClient.token;
    if (token == null) return;

    final uri = Uri.parse(
      '${AppConfig.wsBaseUrl}/api/v1/anomaly/ws/admin?token=$token',
    );

    try {
      _wsChannel = WebSocketChannel.connect(uri);
      _wsSubscription = _wsChannel!.stream.listen(
        _onWsMessage,
        onError: (_) {},   // non-fatal — REST data is still displayed
        onDone: () {},
        cancelOnError: false,
      );
    } catch (_) {
      // WS connection failure must never crash the screen.
    }
  }

  void _onWsMessage(dynamic raw) {
    try {
      final data = json.decode(raw as String) as Map<String, dynamic>;
      if (data['type'] != 'anomaly_alert') return;

      // Reconstruct a card-compatible alert map from the flat WS payload.
      final newAlert = <String, dynamic>{
        'id': data['alert_id'],
        'user_id': data['user_id'],
        'anomaly_score': data['anomaly_score'],
        'severity': data['severity'],
        'explanation': data['explanation'],
        'top_features': data['top_features'] ?? [],
        'is_acknowledged': false,
        'created_at': data['timestamp'],
      };

      setState(() {
        _alerts.insert(0, newAlert);
        if (_stats != null) {
          _stats!['total_alerts'] = (_stats!['total_alerts'] as int? ?? 0) + 1;
          _stats!['unacknowledged'] =
              (_stats!['unacknowledged'] as int? ?? 0) + 1;
          if (newAlert['severity'] == 'HIGH') {
            _stats!['high_severity'] =
                (_stats!['high_severity'] as int? ?? 0) + 1;
          }
        }
      });
    } catch (_) {}
  }

  // ---------------------------------------------------------------------------
  // Acknowledge
  // ---------------------------------------------------------------------------

  Future<void> _acknowledgeAlert(int alertId) async {
    setState(() => _acknowledgingIds.add(alertId));

    try {
      final response =
          await _apiClient.post('/anomaly/alerts/$alertId/acknowledge', {});
      final updated = Map<String, dynamic>.from(response as Map);

      setState(() {
        final idx = _alerts.indexWhere((a) => a['id'] == alertId);
        if (idx != -1) {
          _alerts[idx] = {..._alerts[idx], ...updated};
        }
        if (_stats != null) {
          final prev = _stats!['unacknowledged'] as int? ?? 0;
          _stats!['unacknowledged'] = prev > 0 ? prev - 1 : 0;
        }
        _acknowledgingIds.remove(alertId);
      });
    } catch (e) {
      setState(() => _acknowledgingIds.remove(alertId));
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to acknowledge: $e')),
        );
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Build
  // ---------------------------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Security Alerts'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading security alerts...');
    }

    if (_error != null) {
      return ErrorMessage(
        message: _error!,
        onRetry: _loadData,
      );
    }

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildStatsBar(),
          const SizedBox(height: 24),
          _buildAlertsList(),
        ],
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Stats bar
  // ---------------------------------------------------------------------------

  Widget _buildStatsBar() {
    if (_stats == null) return const SizedBox.shrink();

    final total = _stats!['total_alerts'] as int? ?? 0;
    final unacknowledged = _stats!['unacknowledged'] as int? ?? 0;
    final high = _stats!['high_severity'] as int? ?? 0;

    return Row(
      children: [
        Expanded(
          child: _buildStatCard(
            icon: Icons.notifications_outlined,
            label: 'Total',
            value: '$total',
            color: Colors.blueGrey,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildStatCard(
            icon: Icons.mark_email_unread_outlined,
            label: 'Unread',
            value: '$unacknowledged',
            color: Colors.orange,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _buildStatCard(
            icon: Icons.warning_amber_outlined,
            label: 'HIGH',
            value: '$high',
            color: Colors.red,
          ),
        ),
      ],
    );
  }

  Widget _buildStatCard({
    required IconData icon,
    required String label,
    required String value,
    required Color color,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 14.0, horizontal: 8.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 24, color: color),
            const SizedBox(height: 6),
            Text(
              value,
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: TextStyle(
                fontSize: 11,
                color: Colors.grey[600],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Alerts list
  // ---------------------------------------------------------------------------

  Widget _buildAlertsList() {
    if (_alerts.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(32.0),
          child: Center(
            child: Column(
              children: [
                Icon(
                  Icons.shield_outlined,
                  size: 64,
                  color: Colors.green[400],
                ),
                const SizedBox(height: 16),
                Text(
                  'No anomaly alerts detected.',
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
            const Text(
              'Alerts',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            Text(
              'Total: ${_alerts.length}',
              style: TextStyle(fontSize: 14, color: Colors.grey[600]),
            ),
          ],
        ),
        const SizedBox(height: 12),
        ..._alerts.map(_buildAlertCard),
      ],
    );
  }

  Widget _buildAlertCard(Map<String, dynamic> alert) {
    final id = alert['id'] as int? ?? 0;
    final userId = alert['user_id'] as int?;
    final severity = alert['severity'] as String? ?? 'LOW';
    final explanation = alert['explanation'] as String? ?? '';
    final score = (alert['anomaly_score'] as num?)?.toDouble() ?? 0.0;
    final isAcknowledged = alert['is_acknowledged'] as bool? ?? false;
    final createdAtRaw = alert['created_at'] as String?;
    final createdAt =
        createdAtRaw != null ? DateTime.tryParse(createdAtRaw) : null;
    final isAcknowledging = _acknowledgingIds.contains(id);

    final severityColor = _severityColor(severity);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Header: badge + score + timestamp ──────────────────────────
            Row(
              children: [
                _buildSeverityBadge(severity, severityColor),
                const SizedBox(width: 10),
                Text(
                  'Score: ${(score * 100).round()}%',
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const Spacer(),
                if (createdAt != null)
                  Text(
                    DateFormatter.formatDateTime(createdAt),
                    style: TextStyle(fontSize: 11, color: Colors.grey[500]),
                  ),
              ],
            ),
            const SizedBox(height: 10),
            // ── Explanation ─────────────────────────────────────────────────
            Text(explanation, style: const TextStyle(fontSize: 14)),
            const SizedBox(height: 8),
            if (userId != null)
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton.icon(
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) =>
                            BehavioralScoreTrendScreen(userId: userId),
                      ),
                    );
                  },
                  icon: const Icon(Icons.show_chart, size: 16),
                  label: const Text('View Score Trend'),
                  style: TextButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    minimumSize: Size.zero,
                    tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  ),
                ),
              ),
            const SizedBox(height: 4),
            // ── Acknowledge / acknowledged indicator ────────────────────────
            if (!isAcknowledged)
              Align(
                alignment: Alignment.centerRight,
                child: isAcknowledging
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : OutlinedButton.icon(
                        onPressed: () => _acknowledgeAlert(id),
                        icon: const Icon(Icons.check, size: 16),
                        label: const Text('Acknowledge'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: severityColor,
                          side: BorderSide(color: severityColor),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 8,
                          ),
                          textStyle: const TextStyle(fontSize: 13),
                        ),
                      ),
              )
            else
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Icon(Icons.check_circle, size: 14, color: Colors.green[600]),
                  const SizedBox(width: 4),
                  Text(
                    'Acknowledged',
                    style: TextStyle(fontSize: 12, color: Colors.green[600]),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  Widget _buildSeverityBadge(String severity, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color, width: 1),
      ),
      child: Text(
        severity,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.bold,
          color: color,
        ),
      ),
    );
  }

  Color _severityColor(String severity) {
    switch (severity) {
      case 'HIGH':
        return Colors.red;
      case 'MEDIUM':
        return Colors.orange;
      case 'LOW':
        return Colors.amber.shade700;
      default:
        return Colors.grey;
    }
  }
}
