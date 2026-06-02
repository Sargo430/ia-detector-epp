import 'camera_service_base.dart';

class CameraServiceStub implements CameraServiceBase {
  @override
  Future<void> initialize() async {
    throw UnsupportedError(
      'Plataforma no soportada',
    );
  }

  @override
  Future<void> dispose() async {}
}
