import 'package:flutter/material.dart';

import '../models/detection.dart';

class BoundingBoxOverlay extends StatelessWidget {
  final List<Detection> detections;

  const BoundingBoxOverlay({
    super.key,
    required this.detections,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (_, constraints) {
        return CustomPaint(
          size: Size(
            constraints.maxWidth,
            constraints.maxHeight,
          ),
          painter: _BoundingBoxPainter(
            detections,
          ),
        );
      },
    );
  }
}

class _BoundingBoxPainter extends CustomPainter {
  final List<Detection> detections;

  _BoundingBoxPainter(
    this.detections,
  );

  Color _getColor(String cls) {
    switch (cls) {
      case 'Hardhat':
      case 'Safety Vest':
      case 'Mask':
        return Colors.green;

      case 'NO-Hardhat':
      case 'NO-Safety Vest':
      case 'NO-Mask':
        return Colors.red;

      case 'Person':
        return Colors.blue;

      case 'vehicle':
        return Colors.orange;

      case 'machinery':
        return Colors.purple;

      default:
        return Colors.white;
    }
  }

  @override
  void paint(
    Canvas canvas,
    Size size,
  ) {
    for (final detection in detections) {
      if (detection.bbox.length != 4) continue;

      final color = _getColor(
        detection.className,
      );

      final paint = Paint()
        ..color = color
        ..strokeWidth = 3
        ..style = PaintingStyle.stroke;

      final x1 = detection.bbox[0];
      final y1 = detection.bbox[1];
      final x2 = detection.bbox[2];
      final y2 = detection.bbox[3];

      final rect = Rect.fromLTRB(
        x1,
        y1,
        x2,
        y2,
      );

      canvas.drawRect(
        rect,
        paint,
      );

      final textPainter = TextPainter(
        text: TextSpan(
          text:
              '${detection.className} ${(detection.confidence * 100).toStringAsFixed(0)}%',
          style: TextStyle(
            color: color,
            fontSize: 14,
            fontWeight: FontWeight.bold,
            backgroundColor: Colors.black87,
          ),
        ),
        textDirection: TextDirection.ltr,
      );

      textPainter.layout();

      textPainter.paint(
        canvas,
        Offset(
          x1,
          y1 - 18,
        ),
      );
    }
  }

  @override
  bool shouldRepaint(
    covariant CustomPainter oldDelegate,
  ) {
    return true;
  }
}
