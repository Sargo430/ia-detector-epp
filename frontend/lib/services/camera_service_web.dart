// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

import 'camera_service_base.dart';

class CameraServiceWeb implements CameraServiceBase {
  html.VideoElement? videoElement;

  html.MediaStream? stream;

  @override
  Future<void> initialize() async {
    stream = await html.window.navigator.mediaDevices!.getUserMedia({
      'video': true,
      'audio': false,
    });

    videoElement = html.VideoElement()
      ..autoplay = true
      ..muted = true
      ..srcObject = stream;
  }

  @override
  Future<void> dispose() async {
    stream?.getTracks().forEach(
          (track) => track.stop(),
        );
  }
}
