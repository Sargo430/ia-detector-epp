import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/theme/app_theme.dart';

import 'providers/theme_provider.dart';
import 'providers/detection_provider.dart';
import 'providers/camera_provider.dart';

import 'router/app_router.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => ThemeProvider(),
        ),
        ChangeNotifierProvider(
          create: (_) => DetectionProvider(),
        ),
        ChangeNotifierProvider(
          create: (_) => CameraProvider(),
        ),
      ],
      child: const DetectorEPPApp(),
    ),
  );
}

class DetectorEPPApp extends StatelessWidget {
  const DetectorEPPApp({super.key});

  @override
  Widget build(BuildContext context) {
    final themeProvider = context.watch<ThemeProvider>();

    return MaterialApp.router(
      debugShowCheckedModeBanner: false,
      title: 'Detector EPP',
      theme: AppTheme.lightTheme(),
      darkTheme: AppTheme.darkTheme(),
      themeMode: themeProvider.themeMode,
      routerConfig: AppRouter.router,
    );
  }
}
