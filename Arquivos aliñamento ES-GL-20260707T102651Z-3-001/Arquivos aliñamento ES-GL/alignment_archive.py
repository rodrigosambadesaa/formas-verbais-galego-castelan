from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


EXPECTED_FILES = {
    "cba_ES-GL.txt": 4,
    "cba_log.txt": None,
    "cba_pro_ES-GL.txt": 4,
    "cba_ts_ES-GL.txt": 4,
    "cba_ts_log.txt": None,
    "cba_ts_pro_ES-GL.txt": 4,
    "con_vbal_def_es.txt": None,
    "con_vbal_def_gl.txt": None,
    "con_vbal_es.txt": None,
    "con_vbal_gl.txt": None,
    "con_vbal.txt": None,
    "listaVerbos.txt": 1,
    "pal_conf.txt": 3,
    "verbos-es-gl.txt": 3,
}

WARNING_RE = re.compile(r"^\[!\]", re.MULTILINE)


@dataclass
class FileCheck:
    path: str
    exists: bool
    rows: int = 0
    malformed_rows: int = 0
    empty_fields: int = 0
    trailing_space_fields: int = 0
    sample_errors: list[str] | None = None
    warnings: int = 0


@dataclass
class ArchiveReport:
    root: str
    status: str
    reasons: list[str]
    files: list[FileCheck]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


@dataclass
class CleanResult:
    source: str
    cleaned: str
    rejected: str | None
    written_rows: int
    rejected_rows: int

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def _iter_lines(path: Path) -> Iterable[str]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for line in handle:
            yield line.rstrip("\r\n")


def iter_expected_tabular_files() -> Iterable[tuple[str, int]]:
    for name, expected_columns in EXPECTED_FILES.items():
        if expected_columns is not None:
            yield name, expected_columns


def _check_tabular_file(path: Path, expected_columns: int) -> FileCheck:
    check = FileCheck(path=path.name, exists=True, sample_errors=[])
    for line_number, raw_line in enumerate(_iter_lines(path), start=1):
        if not raw_line:
            continue
        check.rows += 1
        parts = raw_line.split("\t")
        if len(parts) != expected_columns:
            check.malformed_rows += 1
            if len(check.sample_errors) < 5:
                check.sample_errors.append(
                    f"Línea {line_number}: {len(parts)} columnas, esperadas {expected_columns}"
                )
            continue

        for idx, field in enumerate(parts, start=1):
            if field == "":
                check.empty_fields += 1
                if len(check.sample_errors) < 5:
                    check.sample_errors.append(
                        f"Línea {line_number}, columna {idx}: campo vacío"
                    )
            if field != field.strip():
                check.trailing_space_fields += 1
                if len(check.sample_errors) < 5:
                    check.sample_errors.append(
                        f"Línea {line_number}, columna {idx}: espacios sobrantes"
                    )
    return check


def _check_log_file(path: Path) -> FileCheck:
    text = path.read_text(encoding="utf-8", errors="replace")
    return FileCheck(
        path=path.name,
        exists=True,
        rows=text.count("\n") + (1 if text else 0),
        warnings=len(WARNING_RE.findall(text)),
        sample_errors=[],
    )


def clean_tabular_file(source: Path, destination: Path, rejected: Path, expected_columns: int) -> CleanResult:
    destination.parent.mkdir(parents=True, exist_ok=True)
    rejected.parent.mkdir(parents=True, exist_ok=True)

    written_rows = 0
    rejected_rows = 0

    with (
        source.open("r", encoding="utf-8", errors="replace", newline="") as src,
        destination.open("w", encoding="utf-8", newline="\n") as dst,
        rejected.open("w", encoding="utf-8", newline="\n") as rej,
    ):
        rej.write("line_number\treason\traw_line\n")
        for line_number, raw_line in enumerate(src, start=1):
            raw_line = raw_line.rstrip("\r\n")
            if not raw_line:
                continue

            parts = raw_line.split("\t")
            if len(parts) != expected_columns:
                rejected_rows += 1
                rej.write(f"{line_number}\tcolumn_count:{len(parts)}\t{raw_line}\n")
                continue

            cleaned_parts = [field.strip() for field in parts]
            if any(field == "" for field in cleaned_parts):
                rejected_rows += 1
                rej.write(f"{line_number}\tempty_field\t{raw_line}\n")
                continue

            dst.write("\t".join(cleaned_parts) + "\n")
            written_rows += 1

    if rejected_rows == 0:
        rejected.unlink(missing_ok=True)
        rejected_name: str | None = None
    else:
        rejected_name = str(rejected)

    return CleanResult(
        source=str(source),
        cleaned=str(destination),
        rejected=rejected_name,
        written_rows=written_rows,
        rejected_rows=rejected_rows,
    )


def analyze_archive(root: Path, *, include_log_warnings: bool = True) -> ArchiveReport:
    checks: list[FileCheck] = []
    reasons: list[str] = []

    for name, expected_columns in EXPECTED_FILES.items():
        path = root / name
        if not path.exists():
            checks.append(FileCheck(path=name, exists=False, sample_errors=[]))
            reasons.append(f"Falta el archivo esperado {name}.")
            continue

        if expected_columns is None:
            if name.endswith("_log.txt"):
                checks.append(_check_log_file(path))
            else:
                rows = sum(1 for _ in _iter_lines(path))
                checks.append(FileCheck(path=name, exists=True, rows=rows, sample_errors=[]))
            continue

        checks.append(_check_tabular_file(path, expected_columns))

    total_malformed = sum(item.malformed_rows for item in checks)
    total_empty = sum(item.empty_fields for item in checks)
    total_trailing = sum(item.trailing_space_fields for item in checks)
    total_warnings = sum(item.warnings for item in checks)

    if total_malformed:
        reasons.append(f"Hay {total_malformed} filas mal formadas.")
    if total_empty:
        reasons.append(f"Hay {total_empty} campos vacíos.")
    if total_trailing:
        reasons.append(f"Hay {total_trailing} campos con espacios sobrantes.")
    if total_warnings and include_log_warnings:
        reasons.append(f"Los logs contienen {total_warnings} avisos de alineación.")

    status = "bien" if not reasons else "mal"
    return ArchiveReport(root=str(root), status=status, reasons=reasons, files=checks)
