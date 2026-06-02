import 'package:camera/camera.dart';

import 'camera_service_base.dart';

class CameraServiceMobile implements CameraServiceBase {
  CameraController? controller;

  @override
  Future<void> initialize() async {
    final cameras = await availableCameras();

    if (cameras.isEmpty) {
      throw Exception('No se encontraron cámaras');
    }

    controller = CameraController(
      cameras.first,
      ResolutionPreset.medium,
      enableAudio: false,
    );

    await controller!.initialize();
  }

  @override
  Future<void> dispose() async {
    await controller?.dispose();
  }
}
