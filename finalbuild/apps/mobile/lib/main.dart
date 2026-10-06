import 'package:flutter/material.dart';

void main() => runApp(const DiagnosticApp());

class DiagnosticApp extends StatelessWidget {
  const DiagnosticApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'AI Auto Diagnostic',
    theme: ThemeData(useMaterial3: true, brightness: Brightness.dark),
    home: const HomePage(),
  );
}
class HomePage extends StatelessWidget {
  const HomePage({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('AI Auto Diagnostic')),
    body: ListView(padding: const EdgeInsets.all(20), children: [
      FilledButton(onPressed: () {}, child: const Text('New Diagnostic Session')),
      const SizedBox(height: 12),
      OutlinedButton(onPressed: () {}, child: const Text('Connect OBD Device')),
      const SizedBox(height: 24),
      const Text('Offline-first diagnostic device foundation'),
      const SizedBox(height: 8),
      const Text('Custom Android device • OBD / CAN / UDS • Sync / OTA ready'),
    ]),
  );
}
