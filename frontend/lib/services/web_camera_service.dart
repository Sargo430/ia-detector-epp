// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

class WebCameraService {
  static final WebCameraService instance = WebCameraService._();

  WebCameraService._();

  html.VideoElement? videoElement;
}
