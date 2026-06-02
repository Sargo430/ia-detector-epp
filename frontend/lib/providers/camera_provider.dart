import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

import '../services/camera_service.dart';

class CameraProvider extends ChangeNotifier {
  final CameraService _service = CameraService();

  CameraController? get controller => _service.controller;

  bool _loading = false;
  bool get loading => _loading;

  bool _initialized = false;
  bool get initialized => _initialized;

  String? _error;
  String? get error => _error;

  XFile? _capturedImage;
  XFile? get capturedImage => _capturedImage;

  Future<void> initialize() async {
    if (_initialized) return;

    _loading = true;
    _error = null;

    notifyListeners();

    try {
      await _service.initialize();

      _initialized = true;
    } catch (e) {
      _error = e.toString();

      debugPrint(
        'ERROR CAMARA: $e',
      );
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> capture() async {
    try {
      final image = await _service.captureImage();

      if (image != null) {
        _capturedImage = image;

        notifyListeners();
      }
    } catch (e) {
      _error = e.toString();

      notifyListeners();
    }
  }

  Future<void> closeCamera() async {
    await _service.dispose();

    _initialized = false;

    notifyListeners();
  }

  @override
  void dispose() {
    _service.dispose();

    super.dispose();
  }
}
