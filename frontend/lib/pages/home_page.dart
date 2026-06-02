import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../core/constants/app_constants.dart';
import '../providers/theme_provider.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final themeProvider = context.watch<ThemeProvider>();
    final cs = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text(AppConstants.appName),
        actions: [
          IconButton(
            onPressed: themeProvider.toggleTheme,
            icon: Icon(
              themeProvider.isDark ? Icons.light_mode : Icons.dark_mode,
            ),
            tooltip: themeProvider.isDark ? 'Modo claro' : 'Modo oscuro',
          ),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 600),
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Icono principal
                Container(
                  width: 120,
                  height: 120,
                  decoration: BoxDecoration(
                    color: cs.primaryContainer,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    Icons.security_rounded,
                    size: 64,
                    color: cs.onPrimaryContainer,
                  ),
                )
                    .animate()
                    .scale(
                      duration: 500.ms,
                      curve: Curves.elasticOut,
                      begin: const Offset(0.6, 0.6),
                    )
                    .fadeIn(duration: 400.ms),

                const SizedBox(height: 28),

                Text(
                  AppConstants.appName,
                  style: const TextStyle(
                    fontSize: 30,
                    fontWeight: FontWeight.bold,
                  ),
                )
                    .animate()
                    .slideY(
                      begin: 0.2,
                      duration: 400.ms,
                      delay: 100.ms,
                      curve: Curves.easeOut,
                    )
                    .fadeIn(duration: 400.ms, delay: 100.ms),

                const SizedBox(height: 8),

                Text(
                  'Sistema Inteligente de Detección\nde Equipos de Protección Personal',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: cs.onSurfaceVariant,
                    height: 1.5,
                  ),
                )
                    .animate()
                    .fadeIn(duration: 400.ms, delay: 200.ms),

                const SizedBox(height: 48),

                // Botón cámara
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: () => context.push('/camera'),
                    icon: const Icon(Icons.camera_alt_rounded),
                    label: const Text('Abrir Cámara'),
                    style: FilledButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                  ),
                )
                    .animate()
                    .slideY(
                      begin: 0.3,
                      duration: 400.ms,
                      delay: 300.ms,
                      curve: Curves.easeOut,
                    )
                    .fadeIn(duration: 400.ms, delay: 300.ms),

                const SizedBox(height: 14),

                // Botón subir
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: () => context.push('/upload'),
                    icon: const Icon(Icons.upload_rounded),
                    label: const Text('Subir Imagen'),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                  ),
                )
                    .animate()
                    .slideY(
                      begin: 0.3,
                      duration: 400.ms,
                      delay: 400.ms,
                      curve: Curves.easeOut,
                    )
                    .fadeIn(duration: 400.ms, delay: 400.ms),

                const SizedBox(height: 40),

                // Versión
                Text(
                  'v${AppConstants.appVersion}',
                  style: TextStyle(
                    fontSize: 12,
                    color: cs.outline,
                  ),
                ).animate().fadeIn(duration: 400.ms, delay: 600.ms),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
