import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../providers/detection_provider.dart';

class UploadPage extends StatefulWidget {
  const UploadPage({super.key});

  @override
  State<UploadPage> createState() => _UploadPageState();
}

class _UploadPageState extends State<UploadPage> {
  Uint8List? _previewBytes;
  String? _filename;
  bool _picking = false;

  final ImagePicker _picker = ImagePicker();

  // ── selección de imagen ────────────────────────────────────────────────────

  Future<void> _pickFromGallery() async {
    await _pick(ImageSource.gallery);
  }

  Future<void> _pickFromCamera() async {
    await _pick(ImageSource.camera);
  }

  Future<void> _pick(ImageSource source) async {
    if (_picking) return;

    setState(() => _picking = true);

    try {
      final XFile? file = await _picker.pickImage(
        source: source,
        imageQuality: 90,
        maxWidth: 1280,
      );

      if (file == null) return;

      final bytes = await file.readAsBytes();

      setState(() {
        _previewBytes = bytes;
        _filename = file.name;
      });
    } catch (e) {
      if (!mounted) return;
      _showError('No se pudo cargar la imagen: $e');
    } finally {
      if (mounted) setState(() => _picking = false);
    }
  }

  // ── detección ──────────────────────────────────────────────────────────────

  Future<void> _detect() async {
    if (_previewBytes == null) return;

    final provider = context.read<DetectionProvider>();
    provider.setImageBytes(_previewBytes!, filename: _filename ?? 'image.jpg');

    await provider.detectImage();

    if (!mounted) return;

    if (provider.state == DetectionState.success ||
        provider.state == DetectionState.error) {
      context.push('/results');
    } else if (provider.state == DetectionState.offline) {
      _showError('Sin conexión al servidor. Verifica que el backend esté activo.');
    }
  }

  void _showError(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: Colors.red.shade700,
      ),
    );
  }

  void _clearImage() {
    setState(() {
      _previewBytes = null;
      _filename = null;
    });
    context.read<DetectionProvider>().reset();
  }

  // ── UI ─────────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<DetectionProvider>();
    final isLoading = provider.state == DetectionState.loading;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Subir Imagen'),
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 600),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // ── área de previsualización ─────────────────────────────────
                _buildPreview(),

                const SizedBox(height: 28),

                // ── botones de selección ─────────────────────────────────────
                if (_previewBytes == null) ...[
                  _PickButton(
                    icon: Icons.photo_library_outlined,
                    label: 'Elegir de galería',
                    onTap: _picking ? null : _pickFromGallery,
                  ),
                  const SizedBox(height: 12),
                  _PickButton(
                    icon: Icons.camera_alt_outlined,
                    label: 'Tomar foto',
                    outlined: true,
                    onTap: _picking ? null : _pickFromCamera,
                  ),
                ] else ...[
                  // ── botón analizar ────────────────────────────────────────
                  FilledButton.icon(
                    onPressed: isLoading ? null : _detect,
                    icon: isLoading
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.search),
                    label: Text(isLoading ? 'Analizando…' : 'Analizar imagen'),
                  ),
                  const SizedBox(height: 12),
                  TextButton.icon(
                    onPressed: isLoading ? null : _clearImage,
                    icon: const Icon(Icons.close),
                    label: const Text('Cambiar imagen'),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPreview() {
    if (_previewBytes == null) {
      return Container(
        height: 260,
        width: double.infinity,
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: Theme.of(context).colorScheme.outlineVariant,
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.image_outlined,
              size: 64,
              color: Theme.of(context).colorScheme.outline,
            ),
            const SizedBox(height: 12),
            Text(
              'Ninguna imagen seleccionada',
              style: TextStyle(
                color: Theme.of(context).colorScheme.outline,
              ),
            ),
          ],
        ),
      );
    }

    return Stack(
      alignment: Alignment.topRight,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(20),
          child: Image.memory(
            _previewBytes!,
            height: 300,
            width: double.infinity,
            fit: BoxFit.cover,
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(8),
          child: CircleAvatar(
            backgroundColor: Colors.black54,
            child: IconButton(
              icon: const Icon(Icons.close, color: Colors.white, size: 18),
              onPressed: _clearImage,
              tooltip: 'Quitar imagen',
            ),
          ),
        ),
        if (_filename != null)
          Positioned(
            bottom: 0,
            left: 0,
            right: 0,
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 12),
              decoration: const BoxDecoration(
                color: Colors.black54,
                borderRadius: BorderRadius.vertical(
                  bottom: Radius.circular(20),
                ),
              ),
              child: Text(
                _filename!,
                style: const TextStyle(color: Colors.white, fontSize: 12),
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ),
      ],
    );
  }
}

// ── Widget auxiliar ──────────────────────────────────────────────────────────

class _PickButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool outlined;
  final VoidCallback? onTap;

  const _PickButton({
    required this.icon,
    required this.label,
    this.outlined = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    if (outlined) {
      return SizedBox(
        width: double.infinity,
        child: OutlinedButton.icon(
          onPressed: onTap,
          icon: Icon(icon),
          label: Text(label),
        ),
      );
    }

    return SizedBox(
      width: double.infinity,
      child: FilledButton.icon(
        onPressed: onTap,
        icon: Icon(icon),
        label: Text(label),
      ),
    );
  }
}
