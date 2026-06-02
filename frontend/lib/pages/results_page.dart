import 'dart:typed_data';
import '../widgets/bounding_box_overlay.dart';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../models/detection.dart';
import '../providers/detection_provider.dart';
import '../services/brightness_service.dart';

class ResultsPage extends StatefulWidget {
  const ResultsPage({super.key});

  @override
  State<ResultsPage> createState() => _ResultsPageState();
}

class _ResultsPageState extends State<ResultsPage> {
  double? _brightness;
  String? _brightnessStatus;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = context.read<DetectionProvider>();
      // Arrancar detección automáticamente si hay bytes pero aún no se procesaron
      if (provider.imageBytes != null &&
          provider.state == DetectionState.initial) {
        provider.detectImage();
      }
    });
    _loadBrightness();
  }

  Future<void> _loadBrightness() async {
    final bytes = context.read<DetectionProvider>().imageBytes;
    if (bytes == null) return;

    final svc = BrightnessService();
    final b = await svc.calculateBrightness(bytes);

    if (mounted) {
      setState(() {
        _brightness = b;
        _brightnessStatus = svc.getStatus(b);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<DetectionProvider>();
    final colorScheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Resultados'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Nueva detección',
            onPressed: () {
              provider.reset();
              context.go('/');
            },
          ),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: _buildBody(provider, colorScheme),
        ),
      ),
    );
  }

  Widget _buildBody(DetectionProvider provider, ColorScheme cs) {
    switch (provider.state) {
      case DetectionState.loading:
        return const _LoadingView();

      case DetectionState.offline:
        return _StatusView(
          icon: Icons.wifi_off_rounded,
          color: cs.error,
          title: 'Sin conexión',
          message:
              'No se pudo conectar al servidor.\nVerifica que el backend esté corriendo en localhost:8000.',
          onAction: () => provider.detectImage(),
          actionLabel: 'Reintentar',
        );

      case DetectionState.error:
        return _StatusView(
          icon: Icons.error_outline_rounded,
          color: cs.error,
          title: 'Error en la detección',
          message: provider.errorMessage ?? 'Error desconocido',
          onAction: () => provider.detectImage(),
          actionLabel: 'Reintentar',
        );

      case DetectionState.success:
        return _ResultsView(
          detections: provider.detections,
          imageBytes: provider.imageBytes,
          brightness: _brightness,
          brightnessStatus: _brightnessStatus,
        );

      case DetectionState.initial:
        return _StatusView(
          icon: Icons.image_search_rounded,
          color: cs.primary,
          title: 'Sin imagen',
          message: 'Selecciona o captura una imagen primero.',
          onAction: () => context.go('/'),
          actionLabel: 'Ir al inicio',
        );
    }
  }
}

// ── Loading ──────────────────────────────────────────────────────────────────

class _LoadingView extends StatelessWidget {
  const _LoadingView();

  @override
  Widget build(BuildContext context) {
    return const Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        CircularProgressIndicator(),
        SizedBox(height: 20),
        Text('Analizando imagen…'),
      ],
    );
  }
}

// ── Status (error / offline / initial) ───────────────────────────────────────

class _StatusView extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String title;
  final String message;
  final VoidCallback? onAction;
  final String? actionLabel;

  const _StatusView({
    required this.icon,
    required this.color,
    required this.title,
    required this.message,
    this.onAction,
    this.actionLabel,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 72, color: color),
          const SizedBox(height: 16),
          Text(title,
              style:
                  const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          Text(message,
              textAlign: TextAlign.center,
              style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant)),
          if (onAction != null) ...[
            const SizedBox(height: 28),
            FilledButton(onPressed: onAction, child: Text(actionLabel!)),
          ],
        ],
      ),
    );
  }
}

// ── Results ───────────────────────────────────────────────────────────────────

class _ResultsView extends StatelessWidget {
  final List<Detection> detections;
  final Uint8List? imageBytes;
  final double? brightness;
  final String? brightnessStatus;

  const _ResultsView({
    required this.detections,
    required this.imageBytes,
    required this.brightness,
    required this.brightnessStatus,
  });

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        // Miniatura
        if (imageBytes != null)
          ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: SizedBox(
                height: 300,
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    Image.memory(
                      imageBytes!,
                      fit: BoxFit.contain,
                    ),
                    BoundingBoxOverlay(
                      detections: detections,
                    ),
                  ],
                ),
              )),

        const SizedBox(height: 20),

        // Brillo
        if (brightnessStatus != null)
          _InfoChip(
            icon: Icons.wb_sunny_outlined,
            label: brightnessStatus!,
            value: brightness?.toStringAsFixed(1),
          ),

        const SizedBox(height: 16),

        // Resumen
        _SummaryCard(detections: detections),

        const SizedBox(height: 16),

        // Lista de detecciones
        if (detections.isEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  Icon(Icons.search_off,
                      size: 48, color: Theme.of(context).colorScheme.outline),
                  const SizedBox(height: 10),
                  const Text('No se detectaron EPP en la imagen',
                      textAlign: TextAlign.center),
                ],
              ),
            ),
          )
        else
          ...detections.map((d) => _DetectionTile(detection: d)),

        const SizedBox(height: 24),

        // Acción
        OutlinedButton.icon(
          onPressed: () {
            context.read<DetectionProvider>().reset();
            context.go('/');
          },
          icon: const Icon(Icons.arrow_back),
          label: const Text('Nueva detección'),
        ),
      ],
    );
  }
}

// ── Summary card ──────────────────────────────────────────────────────────────

class _SummaryCard extends StatelessWidget {
  final List<Detection> detections;

  const _SummaryCard({required this.detections});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final total = detections.length;
    final avgConf = total == 0
        ? 0.0
        : detections.map((d) => d.confidence).reduce((a, b) => a + b) / total;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            _StatItem(
              value: '$total',
              label: 'Detecciones',
              color: cs.primary,
            ),
            const VerticalDivider(width: 40),
            _StatItem(
              value: '${(avgConf * 100).toStringAsFixed(1)}%',
              label: 'Confianza\npromedio',
              color: _confidenceColor(avgConf, cs),
            ),
          ],
        ),
      ),
    );
  }

  Color _confidenceColor(double conf, ColorScheme cs) {
    if (conf >= 0.75) return Colors.green.shade600;
    if (conf >= 0.5) return Colors.orange.shade600;
    return cs.error;
  }
}

class _StatItem extends StatelessWidget {
  final String value;
  final String label;
  final Color color;

  const _StatItem({
    required this.value,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        children: [
          Text(value,
              style: TextStyle(
                  fontSize: 32, fontWeight: FontWeight.bold, color: color)),
          const SizedBox(height: 4),
          Text(label,
              textAlign: TextAlign.center,
              style: TextStyle(
                  fontSize: 12,
                  color: Theme.of(context).colorScheme.onSurfaceVariant)),
        ],
      ),
    );
  }
}

// ── Detection tile ────────────────────────────────────────────────────────────

class _DetectionTile extends StatelessWidget {
  final Detection detection;

  const _DetectionTile({required this.detection});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final pct = detection.confidence * 100;

    Color barColor;
    if (pct >= 75) {
      barColor = Colors.green.shade600;
    } else if (pct >= 50) {
      barColor = Colors.orange.shade600;
    } else {
      barColor = cs.error;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    detection.className,
                    style: const TextStyle(
                        fontWeight: FontWeight.w600, fontSize: 15),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Text(
                  '${pct.toStringAsFixed(1)}%',
                  style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: barColor,
                      fontSize: 15),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: detection.confidence,
                backgroundColor: cs.surfaceContainerHighest,
                valueColor: AlwaysStoppedAnimation<Color>(barColor),
                minHeight: 6,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Info chip ─────────────────────────────────────────────────────────────────

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String label;
  final String? value;

  const _InfoChip({required this.icon, required this.label, this.value});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: cs.secondaryContainer,
        borderRadius: BorderRadius.circular(50),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: cs.onSecondaryContainer),
          const SizedBox(width: 8),
          Text(
            value != null ? '$label · $value' : label,
            style: TextStyle(
                fontSize: 13,
                color: cs.onSecondaryContainer,
                fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }
}
