import 'dart:convert';
import 'package:http/http.dart' as http;

class Api {
  static const base = 'http://10.0.2.2:8000/api'; // эмулятор Android: 10.0.2.2 = хост
  static String? token;

  static Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

  static Future<Map<String, dynamic>> login(String login, String password) async {
    final r = await http.post(Uri.parse('$base/auth/login'),
        headers: _headers,
        body: jsonEncode({'login': login, 'password': password}));
    if (r.statusCode != 200) throw Exception('Ошибка авторизации');
    final data = jsonDecode(r.body);
    token = data['access_token'];
    return data;
  }

  static Future<List<dynamic>> equipment() async {
    final r = await http.get(Uri.parse('$base/equipment/'), headers: _headers);
    if (r.statusCode != 200) throw Exception('Ошибка загрузки');
    return jsonDecode(r.body) as List;
  }

  static Future<List<dynamic>> requests() async {
    final r = await http.get(Uri.parse('$base/requests/'), headers: _headers);
    if (r.statusCode != 200) throw Exception('Ошибка загрузки');
    return jsonDecode(r.body) as List;
  }
}
