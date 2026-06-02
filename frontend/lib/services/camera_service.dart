import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';

class CameraService {
  CameraController? _controller;

  CameraController? get controller => _controller;

  bool _isInitializing = false;

  Future<void> initialize() async {
    if (_isInitializing) return;

    try {
      _isInitializing = true;

      final cameras = await availableCameras();

      debugPrint(
        "TOTAL CAMARAS: ${cameras.length}",
      );

      for (int i = 0; i < cameras.length; i++) {
        debugPrint(
          "CAM[$i] -> ${cameras[i].name} | ${cameras[i].lensDirection}",
        );
      }

      if (cameras.isEmpty) {
        throw Exception(
          'No se encontraron cámaras',
        );
      }

      final selectedCamera = cameras.first;

      debugPrint(
        "CAMARA SELECCIONADA: ${selectedCamera.name}",
      );

      await _controller?.dispose();

      _controller = CameraController(
        selectedCamera,
        ResolutionPreset.medium,
        enableAudio: false,
      );

      debugPrint(
        "INTENTANDO INICIALIZAR CAMARA...",
      );

      await _controller!.initialize();

      debugPrint(
        "CAMARA INICIALIZADA CORRECTAMENTE",
      );
    } on CameraException catch (e) {
      debugPrint(
        "CAMERA ERROR: ${e.code}",
      );

      debugPrint(
        "DESCRIPCION: ${e.description}",
      );

      await _controller?.dispose();
      _controller = null;

      rethrow;
    } finally {
      _isInitializing = false;
    }
  }

  Future<XFile?> captureImage() async {
    try {
      if (_controller == null) {
        return null;
      }

      if (!_controller!.value.isInitialized) {
        return null;
      }

      if (_controller!.value.isTakingPicture) {
        return null;
      }

      return await _controller!.takePicture();
    } catch (e) {
      debugPrint(
        'ERROR CAPTURANDO IMAGEN: $e',
      );

      return null;
    }
  }

  Future<void> dispose() async {
    try {
      await _controller?.dispose();
      _controller = null;
    } catch (_) {}
  }
}
