import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ThemeProvider extends ChangeNotifier {
  bool _isDark = false;

  bool get isDark => _isDark;

  ThemeMode get themeMode => _isDark ? ThemeMode.dark : ThemeMode.light;

  ThemeProvider() {
    loadTheme();
  }

  Future<void> loadTheme() async {
    final prefs = await SharedPreferences.getInstance();

    _isDark = prefs.getBool('darkMode') ?? false;

    notifyListeners();
  }

  Future<void> toggleTheme() async {
    _isDark = !_isDark;

    final prefs = await SharedPreferences.getInstance();

    await prefs.setBool(
      'darkMode',
      _isDark,
    );

    notifyListeners();
  }
}
