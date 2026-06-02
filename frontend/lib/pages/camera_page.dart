import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../providers/camera_provider.dart';
import '../providers/detection_provider.dart';
import '../services/web_capture_service.dart';
import '../widgets/web_camera_view.dart';

class CameraPage extends StatefulWidget {
  const CameraPage({super.key});

  @override
  State<CameraPage> createState() => _CameraPageState();
}

class _CameraPageState extends State<CameraPage> {
  bool _capturing = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!kIsWeb) context.read<CameraProvider>().initialize();
    });
  }

  @override
  void dispose() {
    if (!kIsWeb) context.read<CameraProvider>().closeCamera();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<CameraProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('Cámara')),
      body: _buildBody(provider),
    );
  }

  Widget _buildBody(CameraProvider provider) {
    if (kIsWeb) {
      return _WebCameraBody(
        capturing: _capturing,
        onCapture: _handleWebCapture,
      );
    }

    if (provider.loading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (provider.error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 60),
              const SizedBox(height: 16),
              Text(provider.error!, textAlign: TextAlign.center),
              const SizedBox(height: 20),
              FilledButton(
                onPressed: () => context.read<CameraProvider>().initialize(),
                child: const Text('Reintentar'),
              ),
            ],
          ),
        ),
      );
    }

    final CameraController? controller = provider.controller;
    if (controller == null || !controller.value.isInitialized) {
      return Center(
        child: Text(
          controller == null ? 'Sin cámara disponible' : 'Inicializando cámara…',
        ),
      );
    }

    return Column(
      children: [
        Expanded(child: CameraPreview(controller)),
        Padding(
          padding: const EdgeInsets.all(16),
          child: FilledButton.icon(
            onPressed: _capturing ? null : () => _handleMobileCapture(provider),
            icon: _capturing
                ? const SizedBox(
                    width: 18, height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.camera_alt),
            label: Text(_capturing ? 'Procesando…' : 'Capturar'),
          ),
        ),
      ],
    );
  }

  // ── captura web ─────────────────────────────────────────────────────────────

  Future<void> _handleWebCapture() async {
    if (_capturing) return;
    setState(() => _capturing = true);

    try {
      final bytes = await WebCaptureService.capture();
      if (!mounted) return;

      if (bytes == null) {
        _showSnack('No se pudo capturar la imagen');
        return;
      }

      final detectionProvider = context.read<DetectionProvider>();
      detectionProvider.setImageBytes(bytes, filename: 'captura_web.png');

      // Navegar primero, luego disparar detección desde ResultsPage
      // (el provider ya tiene los bytes, ResultsPage llama detectImage en initState)
      context.push('/results');
    } finally {
      if (mounted) setState(() => _capturing = false);
    }
  }

  // ── captura móvil ───────────────────────────────────────────────────────────

  Future<void> _handleMobileCapture(CameraProvider camProvider) async {
    if (_capturing) return;
    setState(() => _capturing = true);

    try {
      await camProvider.capture();
      if (!mounted) return;

      final xfile = camProvider.capturedImage;
      if (xfile == null) {
        _showSnack('No se pudo capturar la imagen');
        return;
      }

      final bytes = await xfile.readAsBytes();
      if (!mounted) return;

      context.read<DetectionProvider>().setImageBytes(bytes, filename: xfile.name);
      context.push('/results');
    } finally {
      if (mounted) setState(() => _capturing = false);
    }
  }

  void _showSnack(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
  }
}

// ── Widget web separado ──────────────────────────────────────────────────────

class _WebCameraBody extends StatelessWidget {
  final bool capturing;
  final Future<void> Function() onCapture;

  const _WebCameraBody({required this.capturing, required this.onCapture});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        const Expanded(child: WebCameraView()),
        Padding(
          padding: const EdgeInsets.all(16),
          child: FilledButton.icon(
            onPressed: capturing ? null : onCapture,
            icon: capturing
                ? const SizedBox(
                    width: 18, height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.camera_alt),
            label: Text(capturing ? 'Procesando…' : 'Capturar'),
          ),
        ),
      ],
    );
  }
}
