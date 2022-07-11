<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Services\CorpusRepository;
use Illuminate\Http\Request;
use Illuminate\View\View;
use Throwable;

class CorpusController extends Controller
{
    public function __invoke(Request $request, CorpusRepository $repository): View
    {
        $pairSortField = in_array($request->string('pairSortField', 'es')->value(), ['es', 'gl', 'alignmentCount'], true)
            ? $request->string('pairSortField', 'es')->value()
            : 'es';
        $pairSortDirection = $request->string('pairSortDirection', 'asc')->value() === 'desc' ? 'desc' : 'asc';
        $alignmentSortField = in_array($request->string('alignmentSortField', 'pairEs')->value(), ['pairEs', 'pairGl', 'es', 'gl', 'tense', 'person'], true)
            ? $request->string('alignmentSortField', 'pairEs')->value()
            : 'pairEs';
        $alignmentSortDirection = $request->string('alignmentSortDirection', 'asc')->value() === 'desc' ? 'desc' : 'asc';

        $pairSearch = $request->string('pairSearch')->value();
        $alignmentSearch = $request->string('alignmentSearch')->value();
        $selectedTense = $request->string('tense', 'ALL')->value();
        $selectedPerson = $request->string('person', 'ALL')->value();
        $selectedPairKey = $request->string('selectedPair')->value();

        $errorMessage = '';
        $dataset = null;

        try {
            $dataset = $repository->getDataset();
        } catch (Throwable $throwable) {
            $errorMessage = $throwable->getMessage();
        }

        $pairs = [];
        $alignments = [];
        $visibleAlignments = [];
        $selectedPair = null;
        $tenseOptions = [];
        $personOptions = [];
        $hiddenCount = 0;
        $missingAlignments = true;

        if ($dataset !== null) {
            $pairs = $dataset['pairs'];
            $alignments = $dataset['alignments'];
            $tenseOptions = $dataset['tenseOptions'];
            $personOptions = $dataset['personOptions'];
            $missingAlignments = $dataset['missingAlignments'];

            $pairTerms = $this->terms($repository, $pairSearch);
            $pairs = array_values(array_filter($pairs, static function (array $pair) use ($pairTerms): bool {
                foreach ($pairTerms as $term) {
                    if (!str_contains($pair['searchBlob'], $term)) {
                        return false;
                    }
                }

                return true;
            }));

            usort($pairs, function (array $a, array $b) use ($pairSortField, $pairSortDirection, $repository): int {
                $factor = $pairSortDirection === 'asc' ? 1 : -1;
                if ($pairSortField === 'alignmentCount') {
                    $diff = ($a['alignmentCount'] <=> $b['alignmentCount']) * $factor;
                    if ($diff !== 0) {
                        return $diff;
                    }
                } else {
                    $diff = $repository->compareText($a[$pairSortField], $b[$pairSortField]) * $factor;
                    if ($diff !== 0) {
                        return $diff;
                    }
                }

                return $repository->compareText($a['es'], $b['es']) ?: $repository->compareText($a['gl'], $b['gl']);
            });

            foreach ($dataset['pairs'] as $pair) {
                if ($pair['key'] === $selectedPairKey) {
                    $selectedPair = $pair;
                    break;
                }
            }

            $alignmentTerms = $this->terms($repository, $alignmentSearch);
            $usesDefaultAlignmentView = $selectedTense === 'ALL'
                && $selectedPerson === 'ALL'
                && $selectedPair === null
                && $alignmentTerms === []
                && $alignmentSortField === 'pairEs'
                && $alignmentSortDirection === 'asc';

            if ($usesDefaultAlignmentView) {
                $alignments = $dataset['alignments'];
                $visibleAlignments = array_slice($alignments, 0, 300);
                $hiddenCount = max(count($alignments) - count($visibleAlignments), 0);
            } else {
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

                usort($alignments, function (array $a, array $b) use ($alignmentSortField, $alignmentSortDirection, $repository): int {
                    $factor = $alignmentSortDirection === 'asc' ? 1 : -1;
                    $diff = $repository->compareText($a[$alignmentSortField], $b[$alignmentSortField]) * $factor;
                    if ($diff !== 0) {
                        return $diff;
                    }

                    return $repository->compareText($a['pairEs'], $b['pairEs'])
                        ?: $repository->compareText($a['pairGl'], $b['pairGl'])
                        ?: $repository->compareText($a['tense'], $b['tense'])
                        ?: $repository->compareText($a['person'], $b['person'])
                        ?: $repository->compareText($a['es'], $b['es'])
                        ?: $repository->compareText($a['gl'], $b['gl']);
                });

                $visibleAlignments = array_slice($alignments, 0, 300);
                $hiddenCount = max(count($alignments) - count($visibleAlignments), 0);
            }
        }

        return view('corpus', [
            'dataset' => $dataset,
            'pairs' => $pairs,
            'alignments' => $alignments,
            'visibleAlignments' => $visibleAlignments,
            'hiddenCount' => $hiddenCount,
            'selectedPair' => $selectedPair,
            'selectedPairKey' => $selectedPairKey,
            'selectedTense' => $selectedTense,
            'selectedPerson' => $selectedPerson,
            'pairSearch' => $pairSearch,
            'alignmentSearch' => $alignmentSearch,
            'pairSortField' => $pairSortField,
            'pairSortDirection' => $pairSortDirection,
            'alignmentSortField' => $alignmentSortField,
            'alignmentSortDirection' => $alignmentSortDirection,
            'tenseOptions' => $tenseOptions,
            'personOptions' => $personOptions,
            'missingAlignments' => $missingAlignments,
            'errorMessage' => $errorMessage,
        ]);
    }

    private function terms(CorpusRepository $repository, string $value): array
    {
        $normalized = $repository->normalizeText($value);
        if ($normalized === '') {
            return [];
        }

        return array_values(array_filter(explode(' ', $normalized)));
    }
}
