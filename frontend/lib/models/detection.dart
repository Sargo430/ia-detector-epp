class Detection {
  final String className;
  final double confidence;

  final List<double> bbox;

  Detection({
    required this.className,
    required this.confidence,
    required this.bbox,
  });

  factory Detection.fromJson(
    Map<String, dynamic> json,
  ) {
    return Detection(
      className: json['class'] ?? '',
      confidence: (json['confidence'] as num).toDouble(),
      bbox: (json['bbox'] as List<dynamic>? ?? [])
          .map((e) => (e as num).toDouble())
          .toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'class': className,
      'confidence': confidence,
      'bbox': bbox,
    };
  }
}
