<?php

declare(strict_types=1);

namespace App\Services;

class CorpusRepository
{
    public function __construct(
        private readonly ?string $dataDir = null,
    ) {
    }

    public function getDataset(): array
    {
        $dataDir = $this->dataDir ?? (string) config('corpus.data_dir');
        $pairsPath = $dataDir . '/verbos_relacionados.tsv';
        $alignmentsPath = $dataDir . '/alineaciones_completas.tsv';

        if (!is_file($pairsPath)) {
            throw new \RuntimeException('No se encontró verbos_relacionados.tsv');
        }

        $cacheKey = md5(json_encode([
            $pairsPath,
            filemtime($pairsPath),
            filesize($pairsPath),
            $alignmentsPath,
            is_file($alignmentsPath) ? filemtime($alignmentsPath) : null,
            is_file($alignmentsPath) ? filesize($alignmentsPath) : null,
        ], JSON_THROW_ON_ERROR));

        $cacheDir = storage_path('framework/corpus-cache');
        $cacheFile = $cacheDir . '/corpus-' . $cacheKey . '.cache';

        if (is_file($cacheFile)) {
            $cached = unserialize((string) file_get_contents($cacheFile), ['allowed_classes' => false]);
            if (is_array($cached)) {
                return $cached;
            }
        }

        $dataset = $this->parseDataset($pairsPath, $alignmentsPath);

        if (!is_dir($cacheDir)) {
            mkdir($cacheDir, 0777, true);
        }

        file_put_contents($cacheFile, serialize($dataset));

        return $dataset;
    }

    private function parseDataset(string $pairsPath, string $alignmentsPath): array
    {
        $pairAggregates = [];
        $alignments = [];
        $currentPairEs = '';
        $currentPairGl = '';
        $missingAlignments = !is_file($alignmentsPath);

        if (!$missingAlignments) {
            $handle = fopen($alignmentsPath, 'rb');
            if ($handle === false) {
                throw new \RuntimeException('No se pudo abrir alineaciones_completas.tsv');
            }

            while (($line = fgets($handle)) !== false) {
                $line = trim($line);
                if ($line === '') {
                    continue;
                }

                $parts = explode("\t", $line);
                if (count($parts) < 4) {
                    continue;
                }

                [$formEs, $formGl, $tense, $person] = array_map('trim', array_slice($parts, 0, 4));
                if ($tense === 'FN-FN' && $person === 'Inf') {
                    $currentPairEs = $formEs;
                    $currentPairGl = $formGl;
                }

                if ($currentPairEs === '' || $currentPairGl === '') {
                    continue;
                }

                $pairKey = $this->buildPairKey($currentPairEs, $currentPairGl);
                $alignments[] = [
                    'es' => $formEs,
                    'gl' => $formGl,
                    'tense' => $tense,
                    'person' => $person,
                    'pairEs' => $currentPairEs,
                    'pairGl' => $currentPairGl,
                    'pairKey' => $pairKey,
                    'searchBlob' => $this->normalizeText(implode(' ', [$formEs, $formGl, $tense, $person, $currentPairEs, $currentPairGl])),
                ];

                if (!isset($pairAggregates[$pairKey])) {
                    $pairAggregates[$pairKey] = ['count' => 0, 'parts' => []];
                }

                $pairAggregates[$pairKey]['count']++;
                array_push($pairAggregates[$pairKey]['parts'], $formEs, $formGl, $tense, $person);
            }

            fclose($handle);
        }

        $pairs = [];
        $seen = [];
        $handle = fopen($pairsPath, 'rb');
        if ($handle === false) {
            throw new \RuntimeException('No se pudo abrir verbos_relacionados.tsv');
        }

        while (($line = fgets($handle)) !== false) {
            $line = trim($line);
            if ($line === '') {
                continue;
            }

            $parts = explode("\t", $line);
            if (count($parts) < 2) {
                continue;
            }

            $es = trim($parts[0]);
            $gl = trim($parts[1]);
            $key = $this->buildPairKey($es, $gl);

            if (isset($seen[$key])) {
                continue;
            }

            $seen[$key] = true;
            $aggregate = $pairAggregates[$key] ?? ['count' => 0, 'parts' => []];
            $pairs[] = [
                'key' => $key,
                'es' => $es,
                'gl' => $gl,
                'alignmentCount' => $aggregate['count'],
                'searchBlob' => $this->normalizeText($es . ' ' . $gl . ' ' . implode(' ', $aggregate['parts'])),
            ];
        }

        fclose($handle);

        $tenseOptions = array_values(array_unique(array_column($alignments, 'tense')));
        usort($tenseOptions, fn (string $a, string $b): int => $this->compareText($a, $b));
        $personOptions = array_values(array_unique(array_column($alignments, 'person')));
        usort($personOptions, fn (string $a, string $b): int => $this->compareText($a, $b));

        return [
            'pairs' => $pairs,
            'alignments' => $alignments,
            'tenseOptions' => $tenseOptions,
            'personOptions' => $personOptions,
            'missingAlignments' => $missingAlignments,
        ];
    }

    public function normalizeText(string $value): string
    {
        $value = strtr($value, [
            'á' => 'a', 'à' => 'a', 'ä' => 'a', 'â' => 'a', 'ã' => 'a',
            'Á' => 'a', 'À' => 'a', 'Ä' => 'a', 'Â' => 'a', 'Ã' => 'a',
            'é' => 'e', 'è' => 'e', 'ë' => 'e', 'ê' => 'e',
            'É' => 'e', 'È' => 'e', 'Ë' => 'e', 'Ê' => 'e',
            'í' => 'i', 'ì' => 'i', 'ï' => 'i', 'î' => 'i',
            'Í' => 'i', 'Ì' => 'i', 'Ï' => 'i', 'Î' => 'i',
            'ó' => 'o', 'ò' => 'o', 'ö' => 'o', 'ô' => 'o', 'õ' => 'o',
            'Ó' => 'o', 'Ò' => 'o', 'Ö' => 'o', 'Ô' => 'o', 'Õ' => 'o',
            'ú' => 'u', 'ù' => 'u', 'ü' => 'u', 'û' => 'u',
            'Ú' => 'u', 'Ù' => 'u', 'Ü' => 'u', 'Û' => 'u',
        ]);

        $value = preg_replace('/[\x00-\x1F\x7F]/u', ' ', $value) ?? $value;
        $value = preg_replace('/\s+/u', ' ', $value) ?? $value;

        return mb_strtolower(trim($value), 'UTF-8');
    }

    public function buildPairKey(string $es, string $gl): string
    {
        return $this->normalizeText($es) . '|' . $this->normalizeText($gl);
    }

    public function compareText(string $a, string $b): int
    {
        return strcmp($this->normalizeText($a), $this->normalizeText($b));
    }
}
