// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

import 'dart:convert';
import 'dart:typed_data';

import 'web_camera_service.dart';

class WebCaptureService {
  static Future<Uint8List?> capture() async {
    final video = WebCameraService.instance.videoElement;

    if (video == null) {
      return null;
    }

    final canvas = html.CanvasElement(
      width: video.videoWidth,
      height: video.videoHeight,
    );

    final ctx = canvas.context2D;

    ctx.drawImage(
      video,
      0,
      0,
    );

    final dataUrl = canvas.toDataUrl('image/png');

    final base64Data = dataUrl.split(',').last;

    return base64Decode(
      base64Data,
    );
  }
}
