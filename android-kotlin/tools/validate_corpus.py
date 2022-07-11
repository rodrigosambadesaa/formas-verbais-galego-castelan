#!/usr/bin/env python3
"""Validate the canonical TSV inputs before building the APK."""
from pathlib import Path

root = Path(__file__).resolve().parents[2]
pairs = root / "web-angular/src/assets/data/verbos_relacionados.tsv"
forms = root / "formas_verbais_es_gl_completo.txt"
assert pairs.is_file() and forms.is_file(), "Missing canonical corpus inputs"

count_pairs = 0
with pairs.open(encoding="utf-8") as stream:
    for line in stream:
        columns = line.rstrip("\n").split("\t")
        if len(columns) >= 2 and columns[0] and columns[1]:
            count_pairs += 1

count_forms = 0
count_markers = 0
with forms.open(encoding="utf-8") as stream:
    for line in stream:
        columns = line.rstrip("\n").split("\t")
        if len(columns) != 4:
            raise ValueError(f"Unexpected alignment row at {count_forms + 1}")
        count_forms += 1
        if columns[2:] == ["FN-FN", "Inf"]:
            count_markers += 1

assert count_pairs > 100, "Too few infinitive pairs"
assert count_forms > 100 and count_markers > 0, "No usable alignment groups"
print(f"Validated {count_pairs} pairs, {count_forms} forms, {count_markers} group markers")
