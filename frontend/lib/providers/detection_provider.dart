import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../models/detection.dart';
import '../services/api_service.dart';

final ApiService _apiService = ApiService();

enum DetectionState {
  initial,
  loading,
  success,
  error,
  offline,
}

class DetectionProvider extends ChangeNotifier {
  DetectionState _state = DetectionState.initial;
  DetectionState get state => _state;

  /// Bytes de la imagen seleccionada (funciona en web y móvil)
  Uint8List? _imageBytes;
  Uint8List? get imageBytes => _imageBytes;

  String? _imageFilename;
  String? get imageFilename => _imageFilename;

  List<Detection> _detections = [];
  List<Detection> get detections => _detections;

  String? _errorMessage;
  String? get errorMessage => _errorMessage;

  // ── setters de estado ──────────────────────────────────────────────────────

  void setLoading() {
    _state = DetectionState.loading;
    notifyListeners();
  }

  void setSuccess(List<Detection> detections) {
    _detections = detections;
    _state = DetectionState.success;
    notifyListeners();
  }

  void setError(String message) {
    _errorMessage = message;
    _state = DetectionState.error;
    notifyListeners();
  }

  void setOffline() {
    _state = DetectionState.offline;
    notifyListeners();
  }

  /// Guarda los bytes e imagen lista para detectar
  void setImageBytes(Uint8List bytes, {String filename = 'image.jpg'}) {
    _imageBytes = bytes;
    _imageFilename = filename;
    notifyListeners();
  }

  void reset() {
    _imageBytes = null;
    _imageFilename = null;
    _detections = [];
    _errorMessage = null;
    _state = DetectionState.initial;
    notifyListeners();
  }

  // ── lógica principal ───────────────────────────────────────────────────────

  Future<void> detectImage() async {
    if (_imageBytes == null) return;

    try {
      setLoading();

      final response = await _apiService.detectImageBytes(
        _imageBytes!,
        filename: _imageFilename ?? 'image.jpg',
      );

      setSuccess(response.detections);
    } catch (e) {
      final msg = e.toString();
      if (msg.contains('SocketException') ||
          msg.contains('Failed host lookup') ||
          msg.contains('Connection refused')) {
        setOffline();
      } else {
        setError(msg);
      }
    }
  }
}
