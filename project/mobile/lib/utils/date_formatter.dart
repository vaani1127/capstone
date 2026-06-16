import 'package:intl/intl.dart';

/// Utility class for date formatting
class DateFormatter {
  static final DateFormat _dateFormat = DateFormat('MMM dd, yyyy');
  static final DateFormat _timeFormat = DateFormat('hh:mm a');
  static final DateFormat _dateTimeFormat = DateFormat('MMM dd, yyyy hh:mm a');

  /// Format date only
  static String formatDate(DateTime date) {
    return _dateFormat.format(date);
  }

  /// Format time only
  static String formatTime(DateTime date) {
    return _timeFormat.format(date);
  }

  /// Format date and time
  static String formatDateTime(DateTime date) {
    return _dateTimeFormat.format(date);
  }

  /// Get relative time (e.g., "2 hours ago")
  static String getRelativeTime(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inDays > 365) {
      final years = (difference.inDays / 365).floor();
      return '$years ${years == 1 ? 'year' : 'years'} ago';
    } else if (difference.inDays > 30) {
      final months = (difference.inDays / 30).floor();
      return '$months ${months == 1 ? 'month' : 'months'} ago';
    } else if (difference.inDays > 0) {
      return '${difference.inDays} ${difference.inDays == 1 ? 'day' : 'days'} ago';
    } else if (difference.inHours > 0) {
      return '${difference.inHours} ${difference.inHours == 1 ? 'hour' : 'hours'} ago';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes} ${difference.inMinutes == 1 ? 'minute' : 'minutes'} ago';
    } else {
      return 'Just now';
    }
  }

  /// Format waiting time in minutes
  static String formatWaitingTime(int minutes) {
    if (minutes < 60) {
      return '$minutes min';
    } else {
      final hours = minutes ~/ 60;
      final mins = minutes % 60;
      if (mins == 0) {
        return '$hours ${hours == 1 ? 'hour' : 'hours'}';
      }
      return '$hours ${hours == 1 ? 'hour' : 'hours'} $mins min';
    }
  }
}
