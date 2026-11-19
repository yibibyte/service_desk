import 'package:flutter/material.dart';
import 'api.dart';

void main() => runApp(const ServiceDeskApp());

class ServiceDeskApp extends StatelessWidget {
  const ServiceDeskApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Учёт оборудования',
      theme: ThemeData(colorSchemeSeed: Colors.blue, useMaterial3: true),
      home: const LoginScreen(),
    );
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _login = TextEditingController();
  final _password = TextEditingController();

  Future<void> _submit() async {
    try {
      final data = await Api.login(_login.text, _password.text);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Здравствуйте, ${data['full_name']}!')));
      Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const EquipmentScreen()));
    } catch (_) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Ошибка авторизации')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Система учёта оборудования')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(children: [
          TextField(controller: _login,
              decoration: const InputDecoration(labelText: 'Логин')),
          TextField(controller: _password, obscureText: true,
              decoration: const InputDecoration(labelText: 'Пароль')),
          const SizedBox(height: 24),
          FilledButton(onPressed: _submit, child: const Text('Войти')),
        ]),
      ),
    );
  }
}

class EquipmentScreen extends StatefulWidget {
  const EquipmentScreen({super.key});

  @override
  State<EquipmentScreen> createState() => _EquipmentScreenState();
}

class _EquipmentScreenState extends State<EquipmentScreen> {
  late Future<List<dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = Api.equipment();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Оборудование')),
      body: FutureBuilder<List<dynamic>>(
        future: _future,
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final items = snapshot.data!;
          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (context, i) {
              final e = items[i];
              return ListTile(
                leading: const Icon(Icons.precision_manufacturing),
                title: Text(e['name']),
                subtitle: Text(e['inventory_number'] + ' · ' + (e['location'] ?? '')),
                trailing: Chip(label: Text(e['status'])),
              );
            },
          );
        },
      ),
    );
  }
}
