/// Organization model representing a healthcare organisation.
class Organization {
  final int id;
  final String name;
  final String? address;
  final String? city;
  final String? state;
  final String? zip;
  final String? phone;
  final double? revenue;
  final double? utilization;
  final double? lat;
  final double? lon;
  final DateTime createdAt;

  Organization({
    required this.id,
    required this.name,
    this.address,
    this.city,
    this.state,
    this.zip,
    this.phone,
    this.revenue,
    this.utilization,
    this.lat,
    this.lon,
    required this.createdAt,
  });

  factory Organization.fromJson(Map<String, dynamic> json) {
    return Organization(
      id: json['id'] as int,
      name: json['name'] as String,
      address: json['address'] as String?,
      city: json['city'] as String?,
      state: json['state'] as String?,
      zip: json['zip'] as String?,
      phone: json['phone'] as String?,
      revenue: (json['revenue'] as num?)?.toDouble(),
      utilization: (json['utilization'] as num?)?.toDouble(),
      lat: (json['lat'] as num?)?.toDouble(),
      lon: (json['lon'] as num?)?.toDouble(),
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  /// Formatted city/state string for list display.
  String get location {
    if (city != null && state != null) return '$city, $state';
    if (city != null) return city!;
    if (state != null) return state!;
    return 'Unknown';
  }

  /// Utilization as a percentage string, e.g. "78.4%".
  String get utilizationLabel =>
      utilization != null ? '${(utilization! * 100).toStringAsFixed(1)}%' : 'N/A';
}
