import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() {
  runApp(const VerbosApp());
}

@immutable
class VerbPair {
  const VerbPair({required this.es, required this.gl});

  final String es;
  final String gl;

  String get key => '${es.toLowerCase()}|${gl.toLowerCase()}';
}

List<VerbPair> parseVerbPairs(String raw) {
  final seen = <String>{};
  final pairs = <VerbPair>[];

  for (final line in raw.split(RegExp(r'\r?\n'))) {
    if (line.trim().isEmpty) {
      continue;
    }

    final parts = line.split('\t');
    if (parts.length < 2) {
      continue;
    }

    final pair = VerbPair(es: parts[0].trim(), gl: parts[1].trim());
    if (pair.es.isEmpty || pair.gl.isEmpty || seen.contains(pair.key)) {
      continue;
    }

    seen.add(pair.key);
    pairs.add(pair);
  }

  pairs.sort((a, b) => a.es.compareTo(b.es));
  return pairs;
}

class VerbosApp extends StatelessWidget {
  const VerbosApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Formas verbais ES-GL',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2563EB),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const VerbosHomePage(),
    );
  }
}

class VerbosHomePage extends StatefulWidget {
  const VerbosHomePage({super.key});

  @override
  State<VerbosHomePage> createState() => _VerbosHomePageState();
}

class _VerbosHomePageState extends State<VerbosHomePage> {
  late final Future<List<VerbPair>> _pairsFuture = _loadPairs();
  final _searchController = TextEditingController();
  String _query = '';

  static const _assetPath = 'assets/data/verbos_relacionados.tsv';

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<List<VerbPair>> _loadPairs() async {
    final raw = await rootBundle.loadString(_assetPath);
    return parseVerbPairs(raw);
  }

  List<VerbPair> _filterPairs(List<VerbPair> pairs) {
    final normalized = _query.trim().toLowerCase();
    if (normalized.isEmpty) {
      return pairs;
    }

    return pairs
        .where((pair) =>
            pair.es.toLowerCase().contains(normalized) ||
            pair.gl.toLowerCase().contains(normalized))
        .toList(growable: false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF0B1220), Color(0xFF102240), Color(0xFF0F172A)],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 980),
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: FutureBuilder<List<VerbPair>>(
                  future: _pairsFuture,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) {
                      return const _LoadingView();
                    }

                    if (snapshot.hasError) {
                      return _ErrorView(message: snapshot.error.toString());
                    }

                    final pairs = snapshot.data ?? const <VerbPair>[];
                    final filteredPairs = _filterPairs(pairs);

                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        _HeroHeader(
                          totalPairs: pairs.length,
                          visiblePairs: filteredPairs.length,
                        ),
                        const SizedBox(height: 16),
                        _SearchBox(
                          controller: _searchController,
                          onChanged: (value) => setState(() => _query = value),
                          onClear: () => setState(() {
                            _searchController.clear();
                            _query = '';
                          }),
                        ),
                        const SizedBox(height: 16),
                        Expanded(
                          child: _VerbPairList(pairs: filteredPairs),
                        ),
                      ],
                    );
                  },
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _HeroHeader extends StatelessWidget {
  const _HeroHeader({required this.totalPairs, required this.visiblePairs});

  final int totalPairs;
  final int visiblePairs;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: const Color(0xCC111F38),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Corpus ES-GL en Flutter',
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: const Color(0xFFE2E8F0),
                  ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Explora pares de infinitivos castellano-galego desde una interfaz Flutter Web ligera y dockerizable.',
            ),
            const SizedBox(height: 16),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                _Metric(label: 'Pares cargados', value: totalPairs),
                _Metric(label: 'Coincidencias', value: visiblePairs),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value});

  final String label;
  final int value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(14),
        color: const Color(0xAA0F1A2F),
        border: Border.all(color: const Color(0x333B82F6)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            value.toString(),
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: const Color(0xFF93C5FD),
                ),
          ),
          Text(label),
        ],
      ),
    );
  }
}

class _SearchBox extends StatelessWidget {
  const _SearchBox({
    required this.controller,
    required this.onChanged,
    required this.onClear,
  });

  final TextEditingController controller;
  final ValueChanged<String> onChanged;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      onChanged: onChanged,
      decoration: InputDecoration(
        filled: true,
        fillColor: const Color(0xCC0F1A2F),
        labelText: 'Buscar infinitivo ES o GL',
        prefixIcon: const Icon(Icons.search),
        suffixIcon: IconButton(
          tooltip: 'Limpiar búsqueda',
          onPressed: onClear,
          icon: const Icon(Icons.close),
        ),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(16)),
      ),
    );
  }
}

class _VerbPairList extends StatelessWidget {
  const _VerbPairList({required this.pairs});

  final List<VerbPair> pairs;

  @override
  Widget build(BuildContext context) {
    if (pairs.isEmpty) {
      return const Center(
        child: Text('No hay pares que coincidan con la búsqueda actual.'),
      );
    }

    return Card(
      color: const Color(0xCC111F38),
      child: ListView.separated(
        padding: const EdgeInsets.all(12),
        itemCount: pairs.length,
        separatorBuilder: (_, __) => const Divider(height: 1),
        itemBuilder: (context, index) {
          final pair = pairs[index];
          return ListTile(
            leading: CircleAvatar(
              backgroundColor: const Color(0xFF2563EB),
              child: Text(pair.es.isEmpty ? '?' : pair.es[0].toUpperCase()),
            ),
            title: Text(pair.es),
            trailing: Text(
              pair.gl,
              style: const TextStyle(
                color: Color(0xFFBFDBFE),
                fontWeight: FontWeight.w600,
              ),
            ),
            subtitle: const Text('Castellano → Galego'),
          );
        },
      ),
    );
  }
}

class _LoadingView extends StatelessWidget {
  const _LoadingView();

  @override
  Widget build(BuildContext context) {
    return const Center(child: CircularProgressIndicator());
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: const Color(0xCC7F1D1D),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Text('No se pudo cargar el corpus: $message'),
      ),
    );
  }
}
