import 'package:flutter/material.dart';

import '../../services/api_client.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';
import '../../utils/date_formatter.dart';

/// Admin-only screen showing a single user's behavioral anomaly score
/// history over time.
///
/// Backed by GET /anomaly/behavioral-scores/{user_id}, which mirrors the
/// exact sustained-trend logic AnomalyService uses to escalate alerts
/// (7 consecutive scores > 0.35), so this screen and the alerting system
/// never disagree about what counts as a trend.
///
/// No charting package dependency is used deliberately (consistent with
/// keeping the stack as-is) - scores are rendered as a simple proportional
/// bar list, most recent first.
class BehavioralScoreTrendScreen extends StatefulWidget {
  final int userId;
  final String? userLabel;

  const BehavioralScoreTrendScreen({
    super.key,
    required this.userId,
    this.userLabel,
  });

  @override
  State<BehavioralScoreTrendScreen> createState() =>
      _BehavioralScoreTrendScreenState();
}

class _BehavioralScoreTrendScreenState
    extends State<BehavioralScoreTrendScreen> {
  final ApiClient _apiClient = ApiClient();

  bool _isLoading = true;
  String? _error;
  List<Map<String, dynamic>> _scores = [];
  double _averageScore = 0.0;
  double _maxScore = 0.0;
  bool _sustainedTrendFlagged = false;

  @override
  void initState() {
    super.initState();
    _loadTrend();
  }

  Future<void> _loadTrend() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final response = await _apiClient
          .get('/anomaly/behavioral-scores/${widget.userId}?limit=30');
      final data = response as Map<String, dynamic>;

      setState(() {
        _scores = (data['scores'] as List)
            .cast<Map<String, dynamic>>();
        _averageScore = (data['average_score'] as num?)?.toDouble() ?? 0.0;
        _maxScore = (data['max_score'] as num?)?.toDouble() ?? 0.0;
        _sustainedTrendFlagged =
            data['sustained_trend_flagged'] as bool? ?? false;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Color _scoreColor(double score) {
    if (score >= 0.50) return Colors.red;
    if (score > 0.35) return Colors.orange;
    return Colors.green;
  }

  @override
  Widget build(BuildContext context) {
    final title = widget.userLabel != null
        ? 'Behavioral Trend — ${widget.userLabel}'
        : 'Behavioral Trend — User #${widget.userId}';

    return Scaffold(
      appBar: AppBar(
        title: Text(title),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _isLoading ? null : _loadTrend,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadTrend,
        child: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading behavioral trend...');
    }
    if (_error != null) {
      return ErrorMessage(message: _error!, onRetry: _loadTrend);
    }
    if (_scores.isEmpty) {
      return ListView(
        children: const [
          SizedBox(height: 80),
          Center(
            child: Text(
              'No behavioral scores recorded yet for this user.',
              style: TextStyle(color: Colors.grey),
            ),
          ),
        ],
      );
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildSummaryCard(),
        const SizedBox(height: 16),
        Text(
          'Score History (most recent first)',
          style: Theme.of(context)
              .textTheme
              .titleMedium
              ?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        ..._scores.map(_buildScoreRow),
      ],
    );
  }

  Widget _buildSummaryCard() {
    return Card(
      color: _sustainedTrendFlagged ? Colors.red[50] : null,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (_sustainedTrendFlagged)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Row(
                  children: [
                    Icon(Icons.warning_amber_rounded, color: Colors.red[700]),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Sustained trend: last 7 scores all exceed 0.35 - '
                        'matches the same threshold AnomalyService uses to '
                        'escalate an alert.',
                        style: TextStyle(
                          color: Colors.red[700],
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStat('Average', _averageScore),
                _buildStat('Peak', _maxScore),
                _buildStat('Samples', null, count: _scores.length),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStat(String label, double? score, {int? count}) {
    return Column(
      children: [
        Text(
          count != null ? '$count' : '${(score! * 100).round()}%',
          style: TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.bold,
            color: count != null ? Colors.black87 : _scoreColor(score!),
          ),
        ),
        const SizedBox(height: 4),
        Text(label, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
      ],
    );
  }

  Widget _buildScoreRow(Map<String, dynamic> entry) {
    final score = (entry['score'] as num?)?.toDouble() ?? 0.0;
    final computedAtRaw = entry['computed_at'] as String?;
    final computedAt =
        computedAtRaw != null ? DateTime.tryParse(computedAtRaw) : null;
    final role = entry['role'] as String? ?? '';
    final color = _scoreColor(score);

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(
            width: 56,
            child: Text(
              '${(score * 100).round()}%',
              style: TextStyle(fontWeight: FontWeight.w600, color: color),
            ),
          ),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: score.clamp(0.0, 1.0),
                minHeight: 10,
                backgroundColor: Colors.grey[200],
                valueColor: AlwaysStoppedAnimation<Color>(color),
              ),
            ),
          ),
          const SizedBox(width: 12),
          SizedBox(
            width: 90,
            child: Text(
              role,
              style: TextStyle(fontSize: 12, color: Colors.grey[600]),
            ),
          ),
          SizedBox(
            width: 90,
            child: Text(
              computedAt != null
                  ? DateFormatter.formatDateTime(computedAt)
                  : '-',
              style: TextStyle(fontSize: 11, color: Colors.grey[500]),
              textAlign: TextAlign.right,
            ),
          ),
        ],
      ),
    );
  }
}
