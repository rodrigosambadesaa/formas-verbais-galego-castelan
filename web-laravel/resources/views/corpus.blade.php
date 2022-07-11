@php
    $baseParams = [
        'pairSearch' => $pairSearch,
        'alignmentSearch' => $alignmentSearch,
        'tense' => $selectedTense,
        'person' => $selectedPerson,
        'selectedPair' => $selectedPairKey,
        'pairSortField' => $pairSortField,
        'pairSortDirection' => $pairSortDirection,
        'alignmentSortField' => $alignmentSortField,
        'alignmentSortDirection' => $alignmentSortDirection,
    ];

    $sortLink = function (string $field, string $label) use ($baseParams, $alignmentSortField, $alignmentSortDirection) {
        $nextDirection = $alignmentSortField === $field && $alignmentSortDirection === 'asc' ? 'desc' : 'asc';
        $arrow = $alignmentSortField !== $field ? '' : ($alignmentSortDirection === 'asc' ? '▲' : '▼');
        $query = http_build_query(array_filter(array_merge($baseParams, [
            'alignmentSortField' => $field,
            'alignmentSortDirection' => $nextDirection,
        ]), fn ($value) => $value !== null && $value !== ''));

        return '<a class="sort-link" href="?' . e($query) . '"><span>' . e($label) . '</span><span>' . $arrow . '</span></a>';
    };
@endphp
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Buscador ES-GL en Laravel</title>
    <link rel="stylesheet" href="{{ asset('styles.css') }}">
</head>
<body>
<main class="page">
    <section class="hero">
        <span class="badge">Corpus ES-GL</span>
        <h1>Buscador total de formas verbales en Laravel</h1>
        <p>La misma consulta integral del corpus, servida desde Laravel con filtros, ordenación y cache de lectura.</p>
        <div class="stats">
            <article><strong>{{ number_format(count($dataset['pairs'] ?? []), 0, ',', '.') }}</strong><div class="muted">Pares de infinitivos</div></article>
            <article><strong>{{ number_format(count($dataset['alignments'] ?? []), 0, ',', '.') }}</strong><div class="muted">Formas alineadas</div></article>
            <article><strong>{{ number_format(count($alignments), 0, ',', '.') }}</strong><div class="muted">Resultados activos</div></article>
        </div>
    </section>

    <section class="layout">
        <aside class="panel">
            <header>
                <div>
                    <h2>Pares relacionados</h2>
                    <small>{{ $pairSearch !== '' ? number_format(count($pairs), 0, ',', '.') . ' pares coinciden' : number_format(count($dataset['pairs'] ?? []), 0, ',', '.') . ' pares disponibles' }}</small>
                </div>
                @if($selectedPair)
                    <span class="pill">{{ $selectedPair['es'] }} → {{ $selectedPair['gl'] }}</span>
                @endif
            </header>

            <form method="get" class="controls">
                <input type="hidden" name="alignmentSearch" value="{{ $alignmentSearch }}">
                <input type="hidden" name="tense" value="{{ $selectedTense }}">
                <input type="hidden" name="person" value="{{ $selectedPerson }}">
                <input type="hidden" name="alignmentSortField" value="{{ $alignmentSortField }}">
                <input type="hidden" name="alignmentSortDirection" value="{{ $alignmentSortDirection }}">
                <input type="text" name="pairSearch" value="{{ $pairSearch }}" placeholder="Buscar infinitivo o cualquier forma ES/GL">
                <div class="controls-inline">
                    <select name="pairSortField">
                        <option value="es" @selected($pairSortField === 'es')>Ordenar por ES</option>
                        <option value="gl" @selected($pairSortField === 'gl')>Ordenar por GL</option>
                        <option value="alignmentCount" @selected($pairSortField === 'alignmentCount')>Ordenar por n.º de formas</option>
                    </select>
                    <select name="pairSortDirection">
                        <option value="asc" @selected($pairSortDirection === 'asc')>A-Z</option>
                        <option value="desc" @selected($pairSortDirection === 'desc')>Z-A</option>
                    </select>
                    <button type="submit">Aplicar</button>
                    <a class="button-link secondary" href="?{{ http_build_query(array_filter([
                        'alignmentSearch' => $alignmentSearch,
                        'tense' => $selectedTense,
                        'person' => $selectedPerson,
                        'pairSortField' => $pairSortField,
                        'pairSortDirection' => $pairSortDirection,
                        'alignmentSortField' => $alignmentSortField,
                        'alignmentSortDirection' => $alignmentSortDirection,
                    ], fn ($value) => $value !== null && $value !== '')) }}">Limpiar selección</a>
                </div>
            </form>

            @if($errorMessage !== '')
                <p class="status error">{{ $errorMessage }}</p>
            @else
                <div class="pair-list">
                    @forelse($pairs as $pair)
                        @php
                            $query = http_build_query(array_filter(array_merge($baseParams, [
                                'selectedPair' => $pair['key'],
                            ]), fn ($value) => $value !== null && $value !== ''));
                        @endphp
                        <a href="?{{ $query }}" @class(['active' => ($selectedPair['key'] ?? '') === $pair['key']])>
                            <span>{{ $pair['es'] }} → {{ $pair['gl'] }}</span>
                            <span class="muted">{{ number_format($pair['alignmentCount'], 0, ',', '.') }} formas</span>
                        </a>
                    @empty
                        <p class="status">No hay pares que coincidan con la búsqueda actual.</p>
                    @endforelse
                </div>
            @endif
        </aside>

        <section class="panel">
            <header>
                <div>
                    <h2>Formas verbales alineadas</h2>
                    <small>Mostrando {{ number_format(count($visibleAlignments), 0, ',', '.') }} de {{ number_format(count($alignments), 0, ',', '.') }} resultados</small>
                </div>
                <span class="muted">Orden {{ $alignmentSortDirection === 'asc' ? 'ascendente' : 'descendente' }} por {{ $alignmentSortField }}</span>
            </header>

            <form method="get" class="grid-controls controls">
                <input type="hidden" name="selectedPair" value="{{ $selectedPairKey }}">
                <input type="hidden" name="pairSearch" value="{{ $pairSearch }}">
                <input type="hidden" name="pairSortField" value="{{ $pairSortField }}">
                <input type="hidden" name="pairSortDirection" value="{{ $pairSortDirection }}">
                <input type="hidden" name="alignmentSortField" value="{{ $alignmentSortField }}">
                <input type="hidden" name="alignmentSortDirection" value="{{ $alignmentSortDirection }}">
                <input type="text" name="alignmentSearch" value="{{ $alignmentSearch }}" placeholder="Buscar forma, tiempo, persona o infinitivo">
                <select name="tense">
                    <option value="ALL">Todos los tiempos</option>
                    @foreach($tenseOptions as $option)
                        <option value="{{ $option }}" @selected($selectedTense === $option)>{{ $option }}</option>
                    @endforeach
                </select>
                <select name="person">
                    <option value="ALL">Todas las personas</option>
                    @foreach($personOptions as $option)
                        <option value="{{ $option }}" @selected($selectedPerson === $option)>{{ $option }}</option>
                    @endforeach
                </select>
                <div class="controls-inline">
                    <button type="submit">Aplicar</button>
                    <a class="button-link secondary" href="?{{ http_build_query(array_filter([
                        'selectedPair' => $selectedPairKey,
                        'pairSearch' => $pairSearch,
                        'pairSortField' => $pairSortField,
                        'pairSortDirection' => $pairSortDirection,
                        'alignmentSortField' => $alignmentSortField,
                        'alignmentSortDirection' => $alignmentSortDirection,
                    ], fn ($value) => $value !== null && $value !== '')) }}">Limpiar filtros</a>
                </div>
            </form>

            @if($missingAlignments)
                <p class="status">No se encontró `alineaciones_completas.tsv`. La búsqueda completa de formas está deshabilitada.</p>
            @elseif($alignments === [])
                <p class="status">No hay formas alineadas que coincidan con los filtros seleccionados.</p>
            @endif

            @if($hiddenCount > 0)
                <p class="status">Hay {{ number_format($hiddenCount, 0, ',', '.') }} resultados adicionales ocultos. Refina la búsqueda para ver una lista más precisa.</p>
            @endif

            <div class="table-wrap">
                <table>
                    <thead>
                    <tr>
                        <th>{!! $sortLink('pairEs', 'Infinitivo ES') !!}</th>
                        <th>{!! $sortLink('pairGl', 'Infinitivo GL') !!}</th>
                        <th>{!! $sortLink('es', 'Forma ES') !!}</th>
                        <th>{!! $sortLink('gl', 'Forma GL') !!}</th>
                        <th>{!! $sortLink('tense', 'Tiempo') !!}</th>
                        <th>{!! $sortLink('person', 'Persona') !!}</th>
                    </tr>
                    </thead>
                    <tbody>
                    @foreach($visibleAlignments as $row)
                        <tr>
                            <td>{{ $row['pairEs'] }}</td>
                            <td>{{ $row['pairGl'] }}</td>
                            <td>{{ $row['es'] }}</td>
                            <td>{{ $row['gl'] }}</td>
                            <td><code>{{ $row['tense'] }}</code></td>
                            <td><code>{{ $row['person'] }}</code></td>
                        </tr>
                    @endforeach
                    </tbody>
                </table>
            </div>
        </section>
    </section>
</main>
</body>
</html>
