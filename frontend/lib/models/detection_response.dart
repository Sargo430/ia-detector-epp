import 'detection.dart';

class DetectionResponse {
  final List<Detection> detections;

  DetectionResponse({
    required this.detections,
  });

  factory DetectionResponse.fromJson(
    Map<String, dynamic> json,
  ) {
    final detections = (json['detections'] as List)
        .map(
          (e) => Detection.fromJson(e),
        )
        .toList();

    return DetectionResponse(
      detections: detections,
    );
  }
}
