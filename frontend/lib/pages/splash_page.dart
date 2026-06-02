import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:go_router/go_router.dart';

class SplashPage extends StatefulWidget {
  const SplashPage({super.key});

  @override
  State<SplashPage> createState() => _SplashPageState();
}

class _SplashPageState extends State<SplashPage> {
  @override
  void initState() {
    super.initState();
    Timer(
      const Duration(milliseconds: 2400),
      () {
        if (mounted) context.go('/');
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;

    return Scaffold(
      backgroundColor: cs.primary,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.security_rounded,
              size: 96,
              color: cs.onPrimary,
            )
                .animate()
                .scale(
                  duration: 600.ms,
                  curve: Curves.elasticOut,
                  begin: const Offset(0.3, 0.3),
                  end: const Offset(1.0, 1.0),
                )
                .fadeIn(duration: 400.ms),

            const SizedBox(height: 24),

            Text(
              'Detector EPP',
              style: TextStyle(
                fontSize: 34,
                fontWeight: FontWeight.bold,
                color: cs.onPrimary,
                letterSpacing: 0.5,
              ),
            )
                .animate()
                .slideY(
                  begin: 0.3,
                  end: 0,
                  duration: 500.ms,
                  delay: 200.ms,
                  curve: Curves.easeOut,
                )
                .fadeIn(duration: 500.ms, delay: 200.ms),

            const SizedBox(height: 10),

            Text(
              'Detección de Equipos de Protección Personal',
              style: TextStyle(
                fontSize: 13,
                color: cs.onPrimary.withOpacity(0.75),
                letterSpacing: 0.3,
              ),
              textAlign: TextAlign.center,
            )
                .animate()
                .fadeIn(duration: 600.ms, delay: 600.ms),

            const SizedBox(height: 60),

            SizedBox(
              width: 28,
              height: 28,
              child: CircularProgressIndicator(
                strokeWidth: 2.5,
                color: cs.onPrimary.withOpacity(0.6),
              ),
            )
                .animate()
                .fadeIn(duration: 400.ms, delay: 900.ms),
          ],
        ),
      ),
    );
  }
}
