import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() {
  runApp(const VerbRelationsApp());
}

class VerbRelationsApp extends StatelessWidget {
  const VerbRelationsApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Relaciones verbales ES-GL',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF55A2FF),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF07111F),
      ),
      home: const VerbExplorerPage(),
    );
  }
}

enum SortDirection { asc, desc }

enum PairSortField { es, gl, alignmentCount }

enum AlignmentSortField { pairEs, pairGl, es, gl, tense, person }

class VerbPair {
  const VerbPair({
    required this.key,
    required this.es,
    required this.gl,
    required this.alignmentCount,
    required this.searchBlob,
  });

  final String key;
  final String es;
  final String gl;
  final int alignmentCount;
  final String searchBlob;
}

class AlignmentRow {
  const AlignmentRow({
    required this.es,
    required this.gl,
    required this.tense,
    required this.person,
    required this.pairEs,
    required this.pairGl,
    required this.pairKey,
    required this.searchBlob,
  });

  final String es;
  final String gl;
  final String tense;
  final String person;
  final String pairEs;
  final String pairGl;
  final String pairKey;
  final String searchBlob;
}

class PairAggregate {
  PairAggregate();

  int count = 0;
  final List<String> parts = <String>[];
}

class ParsedDataset {
  const ParsedDataset({
    required this.pairs,
    required this.alignments,
    required this.tenseOptions,
    required this.personOptions,
    required this.missingAlignments,
  });

  final List<VerbPair> pairs;
  final List<AlignmentRow> alignments;
  final List<String> tenseOptions;
  final List<String> personOptions;
  final bool missingAlignments;
}

class VerbExplorerPage extends StatefulWidget {
  const VerbExplorerPage({super.key});

  @override
  State<VerbExplorerPage> createState() => _VerbExplorerPageState();
}

class _VerbExplorerPageState extends State<VerbExplorerPage> {
  final TextEditingController _pairSearchController = TextEditingController();
  final TextEditingController _alignmentSearchController = TextEditingController();

  bool _loading = true;
  String _errorMessage = '';
  bool _missingAlignments = false;

  List<VerbPair> _pairs = const <VerbPair>[];
  List<VerbPair> _filteredPairs = const <VerbPair>[];
  List<AlignmentRow> _alignments = const <AlignmentRow>[];
  List<AlignmentRow> _filteredAlignments = const <AlignmentRow>[];
  List<String> _tenseOptions = const <String>[];
  List<String> _personOptions = const <String>[];

  VerbPair? _selectedPair;
  String _selectedTense = 'ALL';
  String _selectedPerson = 'ALL';
  PairSortField _pairSortField = PairSortField.es;
  SortDirection _pairSortDirection = SortDirection.asc;
  AlignmentSortField _alignmentSortField = AlignmentSortField.pairEs;
  SortDirection _alignmentSortDirection = SortDirection.asc;

  static const int _maxRows = 300;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void dispose() {
    _pairSearchController.dispose();
    _alignmentSearchController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    try {
      final pairsRaw = await rootBundle.loadString('assets/data/verbos_relacionados.tsv');
      String alignmentsRaw = '';
      bool missingAlignments = false;

      try {
        alignmentsRaw = await rootBundle.loadString('assets/data/alineaciones_completas.tsv');
      } catch (_) {
        missingAlignments = true;
      }

      final dataset = _parseDataset(pairsRaw, alignmentsRaw, missingAlignments);

      if (!mounted) {
        return;
      }

      setState(() {
        _pairs = dataset.pairs;
        _alignments = dataset.alignments;
        _tenseOptions = dataset.tenseOptions;
        _personOptions = dataset.personOptions;
        _missingAlignments = dataset.missingAlignments;
        _loading = false;
      });
      _applyPairFilters();
      _applyAlignmentFilters();
    } catch (_) {
      if (!mounted) {
        return;
      }

      setState(() {
        _loading = false;
        _errorMessage =
            'No se pudieron cargar los datos. Ejecuta tool/sync_assets.ps1 y vuelve a lanzar la app.';
      });
    }
  }

  ParsedDataset _parseDataset(
    String pairsRaw,
    String alignmentsRaw,
    bool missingAlignments,
  ) {
    final pairAggregates = <String, PairAggregate>{};
    final alignments = <AlignmentRow>[];
    String currentPairEs = '';
    String currentPairGl = '';

    for (final line in alignmentsRaw.split(RegExp(r'\r?\n'))) {
      if (line.trim().isEmpty) {
        continue;
      }

      final parts = line.split('\t');
      if (parts.length < 4) {
        continue;
      }

      final formEs = parts[0].trim();
      final formGl = parts[1].trim();
      final tense = parts[2].trim();
      final person = parts[3].trim();

      if (tense == 'FN-FN' && person == 'Inf') {
        currentPairEs = formEs;
        currentPairGl = formGl;
      }

      if (currentPairEs.isEmpty || currentPairGl.isEmpty) {
        continue;
      }

      final pairKey = _buildPairKey(currentPairEs, currentPairGl);
      alignments.add(
        AlignmentRow(
          es: formEs,
          gl: formGl,
          tense: tense,
          person: person,
          pairEs: currentPairEs,
          pairGl: currentPairGl,
          pairKey: pairKey,
          searchBlob: _normalizeText(
            '$formEs $formGl $tense $person $currentPairEs $currentPairGl',
          ),
        ),
      );

      final aggregate = pairAggregates.putIfAbsent(pairKey, PairAggregate.new);
      aggregate.count += 1;
      aggregate.parts.addAll(<String>[formEs, formGl, tense, person]);
    }

    final seen = <String>{};
    final pairs = <VerbPair>[];

    for (final line in pairsRaw.split(RegExp(r'\r?\n'))) {
      if (line.trim().isEmpty) {
        continue;
      }

      final parts = line.split('\t');
      if (parts.length < 2) {
        continue;
      }

      final es = parts[0].trim();
      final gl = parts[1].trim();
      final key = _buildPairKey(es, gl);

      if (!seen.add(key)) {
        continue;
      }

      final aggregate = pairAggregates[key];
      pairs.add(
        VerbPair(
          key: key,
          es: es,
          gl: gl,
          alignmentCount: aggregate?.count ?? 0,
          searchBlob: _normalizeText('$es $gl ${aggregate?.parts.join(' ') ?? ''}'),
        ),
      );
    }

    final tenseOptions = alignments.map((row) => row.tense).toSet().toList()..sort(_compareText);
    final personOptions =
        alignments.map((row) => row.person).toSet().toList()..sort(_compareText);

    return ParsedDataset(
      pairs: pairs,
      alignments: alignments,
      tenseOptions: tenseOptions,
      personOptions: personOptions,
      missingAlignments: missingAlignments,
    );
  }

  static String _normalizeText(String value) {
    const replacements = <String, String>{
      'á': 'a',
      'à': 'a',
      'ä': 'a',
      'â': 'a',
      'ã': 'a',
      'Á': 'a',
      'À': 'a',
      'Ä': 'a',
      'Â': 'a',
      'Ã': 'a',
      'é': 'e',
      'è': 'e',
      'ë': 'e',
      'ê': 'e',
      'É': 'e',
      'È': 'e',
      'Ë': 'e',
      'Ê': 'e',
      'í': 'i',
      'ì': 'i',
      'ï': 'i',
      'î': 'i',
      'Í': 'i',
      'Ì': 'i',
      'Ï': 'i',
      'Î': 'i',
      'ó': 'o',
      'ò': 'o',
      'ö': 'o',
      'ô': 'o',
      'õ': 'o',
      'Ó': 'o',
      'Ò': 'o',
      'Ö': 'o',
      'Ô': 'o',
      'Õ': 'o',
      'ú': 'u',
      'ù': 'u',
      'ü': 'u',
      'û': 'u',
      'Ú': 'u',
      'Ù': 'u',
      'Ü': 'u',
      'Û': 'u',
    };

    final buffer = StringBuffer();
    for (final rune in value.runes) {
      final char = String.fromCharCode(rune);
      buffer.write(replacements[char] ?? char);
    }

    return buffer
        .toString()
        .replaceAll(RegExp(r'[\u0000-\u001F\u007F]'), ' ')
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim()
        .toLowerCase();
  }

  static String _buildPairKey(String es, String gl) => '${_normalizeText(es)}|${_normalizeText(gl)}';

  static int _compareText(String a, String b) => _normalizeText(a).compareTo(_normalizeText(b));

  List<String> _queryTerms(String raw) {
    return _normalizeText(raw).split(RegExp(r'\s+')).where((term) => term.isNotEmpty).toList();
  }

  void _applyPairFilters() {
    final terms = _queryTerms(_pairSearchController.text);
    final filtered = _pairs
        .where((pair) => terms.every((term) => pair.searchBlob.contains(term)))
        .toList()
      ..sort(_comparePairs);

    setState(() {
      _filteredPairs = filtered;
    });
  }

  void _applyAlignmentFilters() {
    final terms = _queryTerms(_alignmentSearchController.text);
    final filtered = _alignments
        .where((row) {
          if (_selectedTense != 'ALL' && row.tense != _selectedTense) {
            return false;
          }
          if (_selectedPerson != 'ALL' && row.person != _selectedPerson) {
            return false;
          }
          if (_selectedPair != null && row.pairKey != _selectedPair!.key) {
            return false;
          }
          return terms.every((term) => row.searchBlob.contains(term));
        })
        .toList()
      ..sort(_compareAlignments);

    setState(() {
      _filteredAlignments = filtered;
    });
  }

  int _comparePairs(VerbPair a, VerbPair b) {
    final factor = _pairSortDirection == SortDirection.asc ? 1 : -1;

    switch (_pairSortField) {
      case PairSortField.alignmentCount:
        final diff = (a.alignmentCount - b.alignmentCount) * factor;
        if (diff != 0) {
          return diff;
        }
        break;
      case PairSortField.es:
        final diff = _compareText(a.es, b.es) * factor;
        if (diff != 0) {
          return diff;
        }
        break;
      case PairSortField.gl:
        final diff = _compareText(a.gl, b.gl) * factor;
        if (diff != 0) {
          return diff;
        }
        break;
    }

    return _compareText(a.es, b.es) != 0 ? _compareText(a.es, b.es) : _compareText(a.gl, b.gl);
  }

  int _compareAlignments(AlignmentRow a, AlignmentRow b) {
    final factor = _alignmentSortDirection == SortDirection.asc ? 1 : -1;
    final diff = _compareText(_alignmentField(a, _alignmentSortField), _alignmentField(b, _alignmentSortField)) *
        factor;

    if (diff != 0) {
      return diff;
    }

    return _compareText(a.pairEs, b.pairEs) != 0
        ? _compareText(a.pairEs, b.pairEs)
        : _compareText(a.es, b.es);
  }

  String _alignmentField(AlignmentRow row, AlignmentSortField field) {
    switch (field) {
      case AlignmentSortField.pairEs:
        return row.pairEs;
      case AlignmentSortField.pairGl:
        return row.pairGl;
      case AlignmentSortField.es:
        return row.es;
      case AlignmentSortField.gl:
        return row.gl;
      case AlignmentSortField.tense:
        return row.tense;
      case AlignmentSortField.person:
        return row.person;
    }
  }

  void _togglePairDirection() {
    setState(() {
      _pairSortDirection =
          _pairSortDirection == SortDirection.asc ? SortDirection.desc : SortDirection.asc;
    });
    _applyPairFilters();
  }

  void _setAlignmentSort(AlignmentSortField field) {
    setState(() {
      if (_alignmentSortField == field) {
        _alignmentSortDirection =
            _alignmentSortDirection == SortDirection.asc ? SortDirection.desc : SortDirection.asc;
      } else {
        _alignmentSortField = field;
        _alignmentSortDirection = SortDirection.asc;
      }
    });
    _applyAlignmentFilters();
  }

  @override
  Widget build(BuildContext context) {
    final visibleAlignments = _filteredAlignments.take(_maxRows).toList();
    final hiddenCount = math.max(_filteredAlignments.length - visibleAlignments.length, 0);

    return Scaffold(
      body: DecoratedBox(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: <Color>[Color(0xFF07111F), Color(0xFF0A1830), Color(0xFF040B16)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: _loading
              ? const Center(child: CircularProgressIndicator())
              : _errorMessage.isNotEmpty
                  ? Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Text(_errorMessage, textAlign: TextAlign.center),
                      ),
                    )
                  : LayoutBuilder(
                      builder: (context, constraints) {
                        final wide = constraints.maxWidth >= 1100;
                        return SingleChildScrollView(
                          padding: const EdgeInsets.all(16),
                          child: Center(
                            child: ConstrainedBox(
                              constraints: const BoxConstraints(maxWidth: 1480),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: <Widget>[
                                  _buildHero(),
                                  const SizedBox(height: 16),
                                  wide
                                      ? Row(
                                          crossAxisAlignment: CrossAxisAlignment.start,
                                          children: <Widget>[
                                            Expanded(
                                              flex: 4,
                                              child: _buildPairsPanel(),
                                            ),
                                            const SizedBox(width: 16),
                                            Expanded(
                                              flex: 8,
                                              child: _buildAlignmentsPanel(
                                                visibleAlignments,
                                                hiddenCount,
                                              ),
                                            ),
                                          ],
                                        )
                                      : Column(
                                          children: <Widget>[
                                            _buildPairsPanel(),
                                            const SizedBox(height: 16),
                                            _buildAlignmentsPanel(visibleAlignments, hiddenCount),
                                          ],
                                        ),
                                ],
                              ),
                            ),
                          ),
                        );
                      },
                    ),
        ),
      ),
    );
  }

  Widget _buildHero() {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
        gradient: const LinearGradient(
          colors: <Color>[Color(0x66205093), Color(0xCC07111F)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(999),
              border: Border.all(color: const Color(0x6672E4FF)),
            ),
            child: const Text('Corpus ES-GL', style: TextStyle(color: Color(0xFF72E4FF))),
          ),
          const SizedBox(height: 12),
          const Text(
            'Buscador total de formas verbales',
            style: TextStyle(fontSize: 34, fontWeight: FontWeight.w800),
          ),
          const SizedBox(height: 8),
          const Text(
            'Busca por infinitivos, formas conjugadas, tiempo o persona y ordena los resultados en la misma experiencia que la web Angular.',
            style: TextStyle(color: Color(0xFFCADCF5)),
          ),
          const SizedBox(height: 18),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: <Widget>[
              _buildStatCard(_pairs.length, 'Pares de infinitivos'),
              _buildStatCard(_alignments.length, 'Formas alineadas'),
              _buildStatCard(_filteredAlignments.length, 'Resultados activos'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard(int value, String label) {
    return Container(
      width: 220,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0x99081120),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            value.toString(),
            style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          Text(label, style: const TextStyle(color: Color(0xFF9BB2D0))),
        ],
      ),
    );
  }

  Widget _buildPairsPanel() {
    return _Panel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Text('Pares relacionados', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 4),
          Text(
            _pairSearchController.text.trim().isEmpty
                ? '${_pairs.length} pares disponibles'
                : '${_filteredPairs.length} pares coinciden',
            style: const TextStyle(color: Color(0xFF9BB2D0)),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _pairSearchController,
            onChanged: (_) => _applyPairFilters(),
            decoration: const InputDecoration(
              hintText: 'Buscar infinitivo o cualquier forma ES/GL',
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: <Widget>[
              SizedBox(
                width: 180,
                child: DropdownButtonFormField<PairSortField>(
                  value: _pairSortField,
                  decoration: const InputDecoration(labelText: 'Orden pares'),
                  items: const <DropdownMenuItem<PairSortField>>[
                    DropdownMenuItem(value: PairSortField.es, child: Text('ES')),
                    DropdownMenuItem(value: PairSortField.gl, child: Text('GL')),
                    DropdownMenuItem(value: PairSortField.alignmentCount, child: Text('N.º formas')),
                  ],
                  onChanged: (value) {
                    if (value == null) {
                      return;
                    }
                    setState(() => _pairSortField = value);
                    _applyPairFilters();
                  },
                ),
              ),
              FilledButton.tonal(
                onPressed: _togglePairDirection,
                child: Text(_pairSortDirection == SortDirection.asc ? 'A-Z' : 'Z-A'),
              ),
              FilledButton(
                onPressed: _selectedPair == null
                    ? null
                    : () {
                        setState(() => _selectedPair = null);
                        _applyAlignmentFilters();
                      },
                child: const Text('Limpiar selección'),
              ),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 520,
            child: _filteredPairs.isEmpty
                ? const Center(child: Text('No hay pares que coincidan con la búsqueda actual.'))
                : ListView.separated(
                    itemCount: _filteredPairs.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (context, index) {
                      final pair = _filteredPairs[index];
                      final active = _selectedPair?.key == pair.key;
                      return InkWell(
                        borderRadius: BorderRadius.circular(18),
                        onTap: () {
                          setState(() => _selectedPair = pair);
                          _applyAlignmentFilters();
                        },
                        child: Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(18),
                            border: Border.all(
                              color: active
                                  ? const Color(0xFF55A2FF)
                                  : Colors.white.withOpacity(0.08),
                            ),
                            gradient: active
                                ? const LinearGradient(
                                    colors: <Color>[Color(0x662F74C9), Color(0xAA081120)],
                                  )
                                : null,
                          ),
                          child: Row(
                            children: <Widget>[
                              Expanded(
                                child: Text('${pair.es} → ${pair.gl}'),
                              ),
                              const SizedBox(width: 12),
                              Text(
                                '${pair.alignmentCount} formas',
                                style: const TextStyle(color: Color(0xFFBFDBFE), fontSize: 12),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildAlignmentsPanel(List<AlignmentRow> visibleAlignments, int hiddenCount) {
    return _Panel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Text('Formas verbales alineadas', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 4),
          Text(
            'Mostrando ${visibleAlignments.length} de ${_filteredAlignments.length} resultados',
            style: const TextStyle(color: Color(0xFF9BB2D0)),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: <Widget>[
              SizedBox(
                width: 320,
                child: TextField(
                  controller: _alignmentSearchController,
                  onChanged: (_) => _applyAlignmentFilters(),
                  decoration: const InputDecoration(
                    hintText: 'Buscar forma, tiempo, persona o infinitivo',
                  ),
                ),
              ),
              SizedBox(
                width: 220,
                child: DropdownButtonFormField<String>(
                  value: _selectedTense,
                  decoration: const InputDecoration(labelText: 'Tiempo'),
                  items: <DropdownMenuItem<String>>[
                    const DropdownMenuItem(value: 'ALL', child: Text('Todos los tiempos')),
                    ..._tenseOptions.map((value) => DropdownMenuItem(value: value, child: Text(value))),
                  ],
                  onChanged: (value) {
                    if (value == null) {
                      return;
                    }
                    setState(() => _selectedTense = value);
                    _applyAlignmentFilters();
                  },
                ),
              ),
              SizedBox(
                width: 220,
                child: DropdownButtonFormField<String>(
                  value: _selectedPerson,
                  decoration: const InputDecoration(labelText: 'Persona'),
                  items: <DropdownMenuItem<String>>[
                    const DropdownMenuItem(value: 'ALL', child: Text('Todas las personas')),
                    ..._personOptions.map((value) => DropdownMenuItem(value: value, child: Text(value))),
                  ],
                  onChanged: (value) {
                    if (value == null) {
                      return;
                    }
                    setState(() => _selectedPerson = value);
                    _applyAlignmentFilters();
                  },
                ),
              ),
              FilledButton.tonal(
                onPressed: () {
                  setState(() {
                    _selectedTense = 'ALL';
                    _selectedPerson = 'ALL';
                    _alignmentSearchController.clear();
                  });
                  _applyAlignmentFilters();
                },
                child: const Text('Limpiar filtros'),
              ),
            ],
          ),
          if (_missingAlignments)
            const Padding(
              padding: EdgeInsets.only(top: 12),
              child: Text(
                'Falta assets/data/alineaciones_completas.tsv. Ejecuta tool/sync_assets.ps1 para habilitar la búsqueda completa.',
                style: TextStyle(color: Color(0xFF9BB2D0)),
              ),
            ),
          if (hiddenCount > 0)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Text(
                'Hay $hiddenCount resultados adicionales ocultos. Refina la búsqueda para una lista más precisa.',
                style: const TextStyle(color: Color(0xFF93C5FD)),
              ),
            ),
          const SizedBox(height: 16),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              columns: <DataColumn>[
                _sortableColumn('Infinitivo ES', AlignmentSortField.pairEs),
                _sortableColumn('Infinitivo GL', AlignmentSortField.pairGl),
                _sortableColumn('Forma ES', AlignmentSortField.es),
                _sortableColumn('Forma GL', AlignmentSortField.gl),
                _sortableColumn('Tiempo', AlignmentSortField.tense),
                _sortableColumn('Persona', AlignmentSortField.person),
              ],
              rows: visibleAlignments
                  .map(
                    (row) => DataRow(
                      cells: <DataCell>[
                        DataCell(Text(row.pairEs)),
                        DataCell(Text(row.pairGl)),
                        DataCell(Text(row.es)),
                        DataCell(Text(row.gl)),
                        DataCell(Text(row.tense)),
                        DataCell(Text(row.person)),
                      ],
                    ),
                  )
                  .toList(),
            ),
          ),
        ],
      ),
    );
  }

  DataColumn _sortableColumn(String label, AlignmentSortField field) {
    final selected = _alignmentSortField == field;
    final arrow = !selected ? '' : _alignmentSortDirection == SortDirection.asc ? ' ▲' : ' ▼';
    return DataColumn(
      label: InkWell(
        onTap: () => _setAlignmentSort(field),
        child: Text('$label$arrow'),
      ),
    );
  }
}

class _Panel extends StatelessWidget {
  const _Panel({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
        gradient: const LinearGradient(
          colors: <Color>[Color(0xEE091426), Color(0xF508101E)],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      padding: const EdgeInsets.all(18),
      child: child,
    );
  }
}
