import 'dart:async';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../services/api_client.dart';

class BetaFeedbackScreen extends StatefulWidget {
  const BetaFeedbackScreen({super.key});

  @override
  State<BetaFeedbackScreen> createState() => _BetaFeedbackScreenState();
}

class _BetaFeedbackScreenState extends State<BetaFeedbackScreen> {
  final _formKey = GlobalKey<FormState>();
  final _message = TextEditingController();
  final _expected = TextEditingController();
  final _actual = TextEditingController();
  String _type = 'bug';
  String _severity = 'medium';
  bool _includeTechnical = false;
  bool _sending = false;
  bool _exitDialogOpen = false;
  bool _discardApproved = false;

  static const _types = {
    'bug': 'Bug',
    'ux_ui': 'UX/UI',
    'ocr': 'OCR/lettura etichetta',
    'barcode': 'Barcode',
    'result_score': 'Risultato/score',
    'performance': 'Performance',
    'suggestion': 'Suggerimento',
    'other': 'Altro',
  };
  static const _severities = {
    'low': 'Bassa',
    'medium': 'Media',
    'high': 'Alta',
    'blocking': 'Bloccante',
  };

  bool get _hasUnsentContent =>
      _message.text.trim().isNotEmpty ||
      _expected.text.trim().isNotEmpty ||
      _actual.text.trim().isNotEmpty;

  @override
  void initState() {
    super.initState();
    _message.addListener(_onFormContentChanged);
    _expected.addListener(_onFormContentChanged);
    _actual.addListener(_onFormContentChanged);
  }

  void _onFormContentChanged() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _message.removeListener(_onFormContentChanged);
    _expected.removeListener(_onFormContentChanged);
    _actual.removeListener(_onFormContentChanged);
    _message.dispose();
    _expected.dispose();
    _actual.dispose();
    super.dispose();
  }

  Future<void> _leaveScreen({bool discard = false}) async {
    if (!mounted) return;
    if (context.canPop()) {
      if (discard) {
        setState(() => _discardApproved = true);
        await WidgetsBinding.instance.endOfFrame;
      }
      if (mounted) context.pop();
      return;
    }
    context.go('/');
  }

  Future<void> _requestExit() async {
    if (_exitDialogOpen || _sending) return;
    if (!_hasUnsentContent) {
      await _leaveScreen();
      return;
    }

    _exitDialogOpen = true;
    final shouldExit = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Uscire senza inviare?'),
        content: const Text('Il feedback inserito verrà perso.'),
        actions: [
          TextButton(
            key: const ValueKey('continue-feedback-editing'),
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Continua a scrivere'),
          ),
          FilledButton(
            key: const ValueKey('discard-feedback'),
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Esci'),
          ),
        ],
      ),
    );
    _exitDialogOpen = false;
    if (shouldExit == true) await _leaveScreen(discard: true);
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _sending = true);
    try {
      await context.read<ApiClient>().submitBetaFeedback(
            feedbackType: _type,
            severity: _severity,
            message: _message.text,
            expectedBehavior: _expected.text,
            actualBehavior: _actual.text,
            includeTechnicalContext: _includeTechnical,
          );
      if (!mounted) return;
      _message.clear();
      _expected.clear();
      _actual.clear();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Feedback inviato. Grazie!')),
      );
    } on Object {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Feedback non inviato. Riprova.')),
      );
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) => PopScope(
        canPop: context.canPop() && (!_hasUnsentContent || _discardApproved),
        onPopInvokedWithResult: (didPop, _) {
          if (!didPop) unawaited(_requestExit());
        },
        child: Scaffold(
          appBar: AppBar(
            title: const Text('Lascia feedback'),
            leading: BackButton(
              key: const ValueKey('feedback-back-button'),
              onPressed: _requestExit,
            ),
          ),
          body: Form(
            key: _formKey,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                DropdownButtonFormField<String>(
                  key: const ValueKey('feedback-type'),
                  initialValue: _type,
                  decoration: const InputDecoration(labelText: 'Tipo feedback'),
                  items: _types.entries
                      .map((e) =>
                          DropdownMenuItem(value: e.key, child: Text(e.value)))
                      .toList(),
                  onChanged: (value) => setState(() => _type = value ?? _type),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  key: const ValueKey('feedback-severity'),
                  initialValue: _severity,
                  decoration: const InputDecoration(labelText: 'Gravità'),
                  items: _severities.entries
                      .map((e) =>
                          DropdownMenuItem(value: e.key, child: Text(e.value)))
                      .toList(),
                  onChanged: (value) =>
                      setState(() => _severity = value ?? _severity),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  key: const ValueKey('feedback-message'),
                  controller: _message,
                  minLines: 4,
                  maxLines: 8,
                  maxLength: 8000,
                  decoration: const InputDecoration(
                      labelText: 'Descrivi il feedback *'),
                  validator: (value) => (value?.trim().length ?? 0) < 5
                      ? 'Scrivi almeno 5 caratteri.'
                      : null,
                ),
                TextFormField(
                  controller: _expected,
                  maxLines: 3,
                  maxLength: 4000,
                  decoration: const InputDecoration(
                      labelText: 'Cosa ti aspettavi? (opzionale)'),
                ),
                TextFormField(
                  controller: _actual,
                  maxLines: 3,
                  maxLength: 4000,
                  decoration: const InputDecoration(
                      labelText: 'Cosa è successo invece? (opzionale)'),
                ),
                CheckboxListTile(
                  value: _includeTechnical,
                  contentPadding: EdgeInsets.zero,
                  title:
                      const Text('Includi informazioni tecniche sanitizzate'),
                  subtitle: const Text(
                      'Non include immagini, barcode o dati dell’etichetta.'),
                  onChanged: (value) =>
                      setState(() => _includeTechnical = value ?? false),
                ),
                const SizedBox(height: 12),
                FilledButton.icon(
                  key: const ValueKey('submit-feedback'),
                  onPressed: _sending ? null : _submit,
                  icon: _sending
                      ? const SizedBox.square(
                          dimension: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.send_outlined),
                  label: const Text('Invia feedback'),
                ),
              ],
            ),
          ),
        ),
      );
}
