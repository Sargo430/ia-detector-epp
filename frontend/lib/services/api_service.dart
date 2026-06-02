import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../core/constants/api_constants.dart';
import '../models/detection_response.dart';

class ApiService {
  /// Envía una imagen al backend y retorna las detecciones.
  /// Acepta [Uint8List] para funcionar tanto en web como en móvil.
  Future<DetectionResponse> detectImageBytes(
    Uint8List imageBytes, {
    String filename = 'image.jpg',
  }) async {
    try {
      final uri = Uri.parse(ApiConstants.detectImage);

      final request = http.MultipartRequest('POST', uri);

      request.files.add(
        http.MultipartFile.fromBytes(
          'image',
          imageBytes,
          filename: filename,
        ),
      );

      final streamedResponse = await request.send().timeout(
            ApiConstants.timeout,
          );

      final response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return DetectionResponse.fromJson(
          jsonDecode(response.body),
        );
      }

      throw Exception('Error API: ${response.statusCode} — ${response.body}');
    } catch (e) {
      debugPrint('ApiService error: $e');
      throw Exception(e.toString());
    }
  }
}
