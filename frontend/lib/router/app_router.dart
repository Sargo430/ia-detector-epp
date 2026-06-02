import 'package:go_router/go_router.dart';

import '../pages/home_page.dart';
import '../pages/camera_page.dart';
import '../pages/upload_page.dart';
import '../pages/results_page.dart';
import '../pages/splash_page.dart';

class AppRouter {
  static final router = GoRouter(
    initialLocation: '/splash',
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashPage(),
      ),
      GoRoute(
        path: '/',
        builder: (context, state) => const HomePage(),
      ),
      GoRoute(
        path: '/camera',
        builder: (context, state) => const CameraPage(),
      ),
      GoRoute(
        path: '/upload',
        builder: (context, state) => const UploadPage(),
      ),
      GoRoute(
        path: '/results',
        builder: (context, state) => const ResultsPage(),
      ),
    ],
  );
}
