import 'dart:typed_data';

import 'package:image/image.dart' as img;

class BrightnessService {
  /// Calcula el brillo promedio de una imagen a partir de sus bytes.
  /// Compatible con web y móvil (no usa dart:io).
  Future<double> calculateBrightness(Uint8List bytes) async {
    final image = img.decodeImage(bytes);

    if (image == null) return 0;

    double total = 0;

    for (int y = 0; y < image.height; y += 10) {
      for (int x = 0; x < image.width; x += 10) {
        final pixel = image.getPixel(x, y);
        total += (pixel.r + pixel.g + pixel.b) / 3;
      }
    }

    final pixels = (image.width / 10) * (image.height / 10);

    return total / pixels;
  }

  String getStatus(double brightness) {
    if (brightness > 180) return 'Buena iluminación';
    if (brightness > 100) return 'Iluminación media';
    return 'Iluminación insuficiente';
  }
}
