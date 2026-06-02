// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'dart:ui_web' as ui;

import 'package:flutter/material.dart';

import '../services/web_camera_service.dart';

class WebCameraView extends StatefulWidget {
  const WebCameraView({super.key});

  @override
  State<WebCameraView> createState() => _WebCameraViewState();
}

class _WebCameraViewState extends State<WebCameraView> {
  // Mapa global: viewId -> videoElement, para que la factory siempre
  // devuelva el elemento correcto aunque el widget se recree.
  static final Map<int, html.VideoElement> _elements = {};
  static bool _factoryRegistered = false;

  html.VideoElement? _videoElement;
  bool _cameraError = false;
  String _errorMessage = '';
  bool _loading = true;

  @override
  void initState() {
    super.initState();

    if (!_factoryRegistered) {
      ui.platformViewRegistry.registerViewFactory(
        'webcam-view',
        (int viewId) {
          // Devuelve el elemento que este viewId registró, o uno vacío.
          return _elements[viewId] ??
              (html.VideoElement()..style.display = 'none');
        },
      );
      _factoryRegistered = true;
    }

    _startCamera();
  }

  Future<void> _startCamera() async {
    setState(() {
      _loading = true;
      _cameraError = false;
    });

    try {
      // Intento 1: cámara trasera (útil en móvil)
      // Intento 2: cualquier cámara disponible
      html.MediaStream? stream;

      try {
        stream = await html.window.navigator.mediaDevices!.getUserMedia({
          'video': {'facingMode': 'environment'},
          'audio': false,
        });
      } catch (_) {
        // facingMode 'environment' no disponible → cualquier cámara
        stream = await html.window.navigator.mediaDevices!.getUserMedia({
          'video': true,
          'audio': false,
        });
      }

      final video = html.VideoElement()
        ..autoplay = true
        ..muted = true
        ..srcObject = stream
        ..style.width = '100%'
        ..style.height = '100%'
        ..style.objectFit = 'cover';

      _videoElement = video;
      WebCameraService.instance.videoElement = video;

      if (mounted) setState(() => _loading = false);
    } catch (e) {
      String msg;
      final err = e.toString().toLowerCase();
      if (err.contains('notallowed') || err.contains('permission')) {
        msg = 'Permiso denegado.\n'
            'Haz clic en el ícono de cámara en la barra de dirección y permite el acceso.';
      } else if (err.contains('notfound') || err.contains('devicenotfound')) {
        msg = 'No se encontró ninguna cámara en este dispositivo.';
      } else if (err.contains('notreadable') || err.contains('trackstart')) {
        msg = 'La cámara está siendo usada por otra aplicación.\n'
            'Ciérrala e intenta de nuevo.';
      } else {
        msg = 'No se pudo acceder a la cámara.\nError: $e';
      }

      if (mounted) {
        setState(() {
          _cameraError = true;
          _errorMessage = msg;
          _loading = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _stopStream();
    WebCameraService.instance.videoElement = null;
    super.dispose();
  }

  void _stopStream() {
    final stream = _videoElement?.srcObject;
    if (stream is html.MediaStream) {
      for (final track in stream.getTracks()) {
        track.stop();
      }
    }
    _videoElement?.srcObject = null;
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;

    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_cameraError) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.videocam_off_rounded, size: 64, color: cs.error),
              const SizedBox(height: 16),
              Text(
                _errorMessage,
                textAlign: TextAlign.center,
                style: const TextStyle(height: 1.5),
              ),
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: _startCamera,
                icon: const Icon(Icons.refresh),
                label: const Text('Reintentar'),
              ),
            ],
          ),
        ),
      );
    }

    // Registrar el elemento en el mapa ANTES de construir el HtmlElementView
    return _VideoViewBuilder(
      videoElement: _videoElement!,
      elements: _elements,
    );
  }
}

// Widget separado para poder capturar el viewId en la factory
class _VideoViewBuilder extends StatefulWidget {
  final html.VideoElement videoElement;
  final Map<int, html.VideoElement> elements;

  const _VideoViewBuilder({
    required this.videoElement,
    required this.elements,
  });

  @override
  State<_VideoViewBuilder> createState() => _VideoViewBuilderState();
}

class _VideoViewBuilderState extends State<_VideoViewBuilder> {
  // Usamos un key único por instancia para forzar un viewId nuevo cada vez
  final String _viewKey =
      'webcam-view-${DateTime.now().microsecondsSinceEpoch}';

  @override
  void initState() {
    super.initState();
    // Re-registrar factory con key único por instancia
    ui.platformViewRegistry.registerViewFactory(
      _viewKey,
      (int viewId) {
        widget.elements[viewId] = widget.videoElement;
        return widget.videoElement;
      },
    );
  }

  @override
  void dispose() {
    // Limpiar entradas del mapa al destruir
    widget.elements.removeWhere((_, v) => v == widget.videoElement);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return HtmlElementView(viewType: _viewKey);
  }
}
