<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/src/CorpusRepository.php';

use VerbosEsGl\CorpusRepository;

$repo = new CorpusRepository();

$pairSortField = in_array($_GET['pairSortField'] ?? 'es', ['es', 'gl', 'alignmentCount'], true)
    ? (string) ($_GET['pairSortField'] ?? 'es')
    : 'es';
$pairSortDirection = ($_GET['pairSortDirection'] ?? 'asc') === 'desc' ? 'desc' : 'asc';
$alignmentSortField = in_array($_GET['alignmentSortField'] ?? 'pairEs', ['pairEs', 'pairGl', 'es', 'gl', 'tense', 'person'], true)
    ? (string) ($_GET['alignmentSortField'] ?? 'pairEs')
    : 'pairEs';
$alignmentSortDirection = ($_GET['alignmentSortDirection'] ?? 'asc') === 'desc' ? 'desc' : 'asc';

$pairSearch = (string) ($_GET['pairSearch'] ?? '');
$alignmentSearch = (string) ($_GET['alignmentSearch'] ?? '');
$selectedTense = (string) ($_GET['tense'] ?? 'ALL');
$selectedPerson = (string) ($_GET['person'] ?? 'ALL');
$selectedPairKey = (string) ($_GET['selectedPair'] ?? '');

$errorMessage = '';
$dataset = null;

try {
    $dataset = $repo->getDataset();
} catch (Throwable $exception) {
    $errorMessage = $exception->getMessage();
}

/**
 * @param array<string, scalar|null> $params
 */
function build_query(array $params): string
{
    return http_build_query(array_filter(
        $params,
        static fn ($value): bool => $value !== null && $value !== ''
    ));
}

/**
 * @return list<string>
 */
function terms(CorpusRepository $repo, string $value): array
{
    $normalized = $repo->normalizeText($value);
    if ($normalized === '') {
        return [];
    }

    return array_values(array_filter(explode(' ', $normalized)));
}

if ($dataset === null) {
    $pairs = [];
    $alignments = [];
    $tenseOptions = [];
    $personOptions = [];
    $selectedPair = null;
    $visibleAlignments = [];
    $hiddenCount = 0;
    $missingAlignments = true;
} else {
    $pairs = $dataset['pairs'];
    $alignments = $dataset['alignments'];
    $tenseOptions = $dataset['tenseOptions'];
    $personOptions = $dataset['personOptions'];
    $missingAlignments = $dataset['missingAlignments'];

    $pairTerms = terms($repo, $pairSearch);
    $pairs = array_values(array_filter($pairs, static function (array $pair) use ($pairTerms): bool {
        foreach ($pairTerms as $term) {
            if (!str_contains($pair['searchBlob'], $term)) {
                return false;
            }
        }

        return true;
    }));

    usort($pairs, static function (array $a, array $b) use ($pairSortField, $pairSortDirection, $repo): int {
        $factor = $pairSortDirection === 'asc' ? 1 : -1;
        if ($pairSortField === 'alignmentCount') {
            $diff = ($a['alignmentCount'] <=> $b['alignmentCount']) * $factor;
            if ($diff !== 0) {
                return $diff;
            }
        } else {
            $diff = $repo->compareText($a[$pairSortField], $b[$pairSortField]) * $factor;
            if ($diff !== 0) {
                return $diff;
            }
        }

        return $repo->compareText($a['es'], $b['es']) ?: $repo->compareText($a['gl'], $b['gl']);
    });

    $selectedPair = null;
    foreach ($pairs as $pair) {
        if ($pair['key'] === $selectedPairKey) {
            $selectedPair = $pair;
            break;
        }
    }

    if ($selectedPair === null && $selectedPairKey !== '') {
        foreach ($dataset['pairs'] as $pair) {
            if ($pair['key'] === $selectedPairKey) {
                $selectedPair = $pair;
                break;
            }
        }
    }

    $alignmentTerms = terms($repo, $alignmentSearch);
    $alignments = array_values(array_filter($alignments, static function (array $row) use (
        $selectedTense,
        $selectedPerson,
        $selectedPair,
        $alignmentTerms
    ): bool {
        if ($selectedTense !== 'ALL' && $row['tense'] !== $selectedTense) {
            return false;
        }

        if ($selectedPerson !== 'ALL' && $row['person'] !== $selectedPerson) {
            return false;
        }

        if ($selectedPair !== null && $row['pairKey'] !== $selectedPair['key']) {
            return false;
        }

        foreach ($alignmentTerms as $term) {
            if (!str_contains($row['searchBlob'], $term)) {
                return false;
            }
        }

        return true;
    }));

    usort($alignments, static function (array $a, array $b) use ($alignmentSortField, $alignmentSortDirection, $repo): int {
        $factor = $alignmentSortDirection === 'asc' ? 1 : -1;
        $diff = $repo->compareText($a[$alignmentSortField], $b[$alignmentSortField]) * $factor;
        if ($diff !== 0) {
            return $diff;
        }

        return $repo->compareText($a['pairEs'], $b['pairEs'])
            ?: $repo->compareText($a['pairGl'], $b['pairGl'])
            ?: $repo->compareText($a['tense'], $b['tense'])
            ?: $repo->compareText($a['person'], $b['person'])
            ?: $repo->compareText($a['es'], $b['es'])
            ?: $repo->compareText($a['gl'], $b['gl']);
    });

    $visibleAlignments = array_slice($alignments, 0, 300);
    $hiddenCount = max(count($alignments) - count($visibleAlignments), 0);
}

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

function alignment_sort_link(string $field, string $label, array $baseParams, string $currentField, string $currentDirection): string
{
    $nextDirection = $currentField === $field && $currentDirection === 'asc' ? 'desc' : 'asc';
    $arrow = $currentField !== $field ? '' : ($currentDirection === 'asc' ? '▲' : '▼');
    $query = build_query(array_merge($baseParams, [
        'alignmentSortField' => $field,
        'alignmentSortDirection' => $nextDirection,
    ]));

    return '<a class="sort-link" href="?' . htmlspecialchars($query, ENT_QUOTES) . '">' .
        '<span>' . htmlspecialchars($label, ENT_QUOTES) . '</span><span>' . $arrow . '</span></a>';
}
?>
<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Buscador ES-GL en PHP puro</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
<main class="page">
    <section class="hero">
        <span class="badge">Corpus ES-GL</span>
        <h1>Buscador total de formas verbales en PHP puro</h1>
        <p>Busca infinitivos o formas conjugadas, filtra por tiempo y persona y ordena los resultados sin depender de JavaScript de framework.</p>
        <div class="stats">
            <article><strong><?= number_format(count($dataset['pairs'] ?? []), 0, ',', '.') ?></strong><div class="muted">Pares de infinitivos</div></article>
            <article><strong><?= number_format(count($dataset['alignments'] ?? []), 0, ',', '.') ?></strong><div class="muted">Formas alineadas</div></article>
            <article><strong><?= number_format(count($alignments ?? []), 0, ',', '.') ?></strong><div class="muted">Resultados activos</div></article>
        </div>
    </section>

    <section class="layout">
        <aside class="panel">
            <header>
                <div>
                    <h2>Pares relacionados</h2>
                    <small><?= $pairSearch !== '' ? number_format(count($pairs), 0, ',', '.') . ' pares coinciden' : number_format(count($dataset['pairs'] ?? []), 0, ',', '.') . ' pares disponibles' ?></small>
                </div>
                <?php if (($selectedPair ?? null) !== null): ?>
                    <span class="pill"><?= htmlspecialchars($selectedPair['es']) ?> → <?= htmlspecialchars($selectedPair['gl']) ?></span>
                <?php endif; ?>
            </header>

            <form method="get" class="controls">
                <input type="hidden" name="alignmentSearch" value="<?= htmlspecialchars($alignmentSearch, ENT_QUOTES) ?>">
                <input type="hidden" name="tense" value="<?= htmlspecialchars($selectedTense, ENT_QUOTES) ?>">
                <input type="hidden" name="person" value="<?= htmlspecialchars($selectedPerson, ENT_QUOTES) ?>">
                <input type="hidden" name="alignmentSortField" value="<?= htmlspecialchars($alignmentSortField, ENT_QUOTES) ?>">
                <input type="hidden" name="alignmentSortDirection" value="<?= htmlspecialchars($alignmentSortDirection, ENT_QUOTES) ?>">
                <input type="text" name="pairSearch" value="<?= htmlspecialchars($pairSearch, ENT_QUOTES) ?>" placeholder="Buscar infinitivo o cualquier forma ES/GL">
                <div class="controls-inline">
                    <select name="pairSortField">
                        <option value="es" <?= $pairSortField === 'es' ? 'selected' : '' ?>>Ordenar por ES</option>
                        <option value="gl" <?= $pairSortField === 'gl' ? 'selected' : '' ?>>Ordenar por GL</option>
                        <option value="alignmentCount" <?= $pairSortField === 'alignmentCount' ? 'selected' : '' ?>>Ordenar por n.º de formas</option>
                    </select>
                    <select name="pairSortDirection">
                        <option value="asc" <?= $pairSortDirection === 'asc' ? 'selected' : '' ?>>A-Z</option>
                        <option value="desc" <?= $pairSortDirection === 'desc' ? 'selected' : '' ?>>Z-A</option>
                    </select>
                    <button type="submit">Aplicar</button>
                    <a class="button-link secondary" href="?<?= htmlspecialchars(build_query([
                        'alignmentSearch' => $alignmentSearch,
                        'tense' => $selectedTense,
                        'person' => $selectedPerson,
                        'pairSortField' => $pairSortField,
                        'pairSortDirection' => $pairSortDirection,
                        'alignmentSortField' => $alignmentSortField,
                        'alignmentSortDirection' => $alignmentSortDirection,
                    ]), ENT_QUOTES) ?>">Limpiar selección</a>
                </div>
            </form>

            <?php if ($errorMessage !== ''): ?>
                <p class="status error"><?= htmlspecialchars($errorMessage) ?></p>
            <?php else: ?>
                <div class="pair-list">
                    <?php foreach ($pairs as $pair): ?>
                        <?php
                        $query = build_query(array_merge($baseParams, [
                            'selectedPair' => $pair['key'],
                        ]));
                        $active = ($selectedPair['key'] ?? '') === $pair['key'];
                        ?>
                        <a href="?<?= htmlspecialchars($query, ENT_QUOTES) ?>" class="<?= $active ? 'active' : '' ?>">
                            <span><?= htmlspecialchars($pair['es']) ?> → <?= htmlspecialchars($pair['gl']) ?></span>
                            <span class="muted"><?= number_format($pair['alignmentCount'], 0, ',', '.') ?> formas</span>
                        </a>
                    <?php endforeach; ?>
                    <?php if ($pairs === []): ?>
                        <p class="status">No hay pares que coincidan con la búsqueda actual.</p>
                    <?php endif; ?>
                </div>
            <?php endif; ?>
        </aside>

        <section class="panel">
            <header>
                <div>
                    <h2>Formas verbales alineadas</h2>
                    <small>Mostrando <?= number_format(count($visibleAlignments), 0, ',', '.') ?> de <?= number_format(count($alignments), 0, ',', '.') ?> resultados</small>
                </div>
                <span class="muted">Orden <?= $alignmentSortDirection === 'asc' ? 'ascendente' : 'descendente' ?> por <?= htmlspecialchars($alignmentSortField) ?></span>
            </header>

            <form method="get" class="grid-controls controls">
                <input type="hidden" name="selectedPair" value="<?= htmlspecialchars($selectedPairKey, ENT_QUOTES) ?>">
                <input type="hidden" name="pairSearch" value="<?= htmlspecialchars($pairSearch, ENT_QUOTES) ?>">
                <input type="hidden" name="pairSortField" value="<?= htmlspecialchars($pairSortField, ENT_QUOTES) ?>">
                <input type="hidden" name="pairSortDirection" value="<?= htmlspecialchars($pairSortDirection, ENT_QUOTES) ?>">
                <input type="hidden" name="alignmentSortField" value="<?= htmlspecialchars($alignmentSortField, ENT_QUOTES) ?>">
                <input type="hidden" name="alignmentSortDirection" value="<?= htmlspecialchars($alignmentSortDirection, ENT_QUOTES) ?>">
                <input type="text" name="alignmentSearch" value="<?= htmlspecialchars($alignmentSearch, ENT_QUOTES) ?>" placeholder="Buscar forma, tiempo, persona o infinitivo">
                <select name="tense">
                    <option value="ALL">Todos los tiempos</option>
                    <?php foreach ($tenseOptions as $option): ?>
                        <option value="<?= htmlspecialchars($option, ENT_QUOTES) ?>" <?= $selectedTense === $option ? 'selected' : '' ?>><?= htmlspecialchars($option) ?></option>
                    <?php endforeach; ?>
                </select>
                <select name="person">
                    <option value="ALL">Todas las personas</option>
                    <?php foreach ($personOptions as $option): ?>
                        <option value="<?= htmlspecialchars($option, ENT_QUOTES) ?>" <?= $selectedPerson === $option ? 'selected' : '' ?>><?= htmlspecialchars($option) ?></option>
                    <?php endforeach; ?>
                </select>
                <div class="controls-inline">
                    <button type="submit">Aplicar</button>
                    <a class="button-link secondary" href="?<?= htmlspecialchars(build_query([
                        'selectedPair' => $selectedPairKey,
                        'pairSearch' => $pairSearch,
                        'pairSortField' => $pairSortField,
                        'pairSortDirection' => $pairSortDirection,
                        'alignmentSortField' => $alignmentSortField,
                        'alignmentSortDirection' => $alignmentSortDirection,
                    ]), ENT_QUOTES) ?>">Limpiar filtros</a>
                </div>
            </form>

            <?php if ($missingAlignments): ?>
                <p class="status">No se encontró `alineaciones_completas.tsv`. La búsqueda completa de formas está deshabilitada.</p>
            <?php elseif ($alignments === []): ?>
                <p class="status">No hay formas alineadas que coincidan con los filtros seleccionados.</p>
            <?php endif; ?>

            <?php if ($hiddenCount > 0): ?>
                <p class="status">Hay <?= number_format($hiddenCount, 0, ',', '.') ?> resultados adicionales ocultos. Refina la búsqueda para ver una lista más precisa.</p>
            <?php endif; ?>

            <div class="table-wrap">
                <table>
                    <thead>
                    <tr>
                        <th><?= alignment_sort_link('pairEs', 'Infinitivo ES', $baseParams, $alignmentSortField, $alignmentSortDirection) ?></th>
                        <th><?= alignment_sort_link('pairGl', 'Infinitivo GL', $baseParams, $alignmentSortField, $alignmentSortDirection) ?></th>
                        <th><?= alignment_sort_link('es', 'Forma ES', $baseParams, $alignmentSortField, $alignmentSortDirection) ?></th>
                        <th><?= alignment_sort_link('gl', 'Forma GL', $baseParams, $alignmentSortField, $alignmentSortDirection) ?></th>
                        <th><?= alignment_sort_link('tense', 'Tiempo', $baseParams, $alignmentSortField, $alignmentSortDirection) ?></th>
                        <th><?= alignment_sort_link('person', 'Persona', $baseParams, $alignmentSortField, $alignmentSortDirection) ?></th>
                    </tr>
                    </thead>
                    <tbody>
                    <?php foreach ($visibleAlignments as $row): ?>
                        <tr>
                            <td><?= htmlspecialchars($row['pairEs']) ?></td>
                            <td><?= htmlspecialchars($row['pairGl']) ?></td>
                            <td><?= htmlspecialchars($row['es']) ?></td>
                            <td><?= htmlspecialchars($row['gl']) ?></td>
                            <td><code><?= htmlspecialchars($row['tense']) ?></code></td>
                            <td><code><?= htmlspecialchars($row['person']) ?></code></td>
                        </tr>
                    <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </section>
    </section>
</main>
</body>
</html>
