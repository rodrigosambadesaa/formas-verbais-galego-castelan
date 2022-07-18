from __future__ import annotations

import argparse
from pathlib import Path

from alignment_archive import analyze_archive


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida el lote de archivos de alineamiento ES-GL y dicta si está bien o mal."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Carpeta donde están los archivos descargados.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emite el informe completo en JSON.",
    )
    parser.add_argument(
        "--ignore-log-warnings",
        action="store_true",
        help="Ignora los avisos de alineación de los logs al calcular el veredicto.",
    )
    args = parser.parse_args()

    report = analyze_archive(args.root, include_log_warnings=not args.ignore_log_warnings)

    if args.json:
        print(report.to_json())
        return 0

    print(f"Veredicto: {report.status.upper()}")
    print(f"Carpeta: {report.root}")
    if report.reasons:
        print("Motivos:")
        for reason in report.reasons:
            print(f"- {reason}")
    else:
        print("Motivos:")
        print("- No se detectaron incidencias estructurales.")

    print("Resumen por archivo:")
    for item in report.files:
        summary = f"- {item.path}: existe={item.exists}"
        if item.rows:
            summary += f", filas={item.rows}"
        if item.malformed_rows:
            summary += f", mal_formadas={item.malformed_rows}"
        if item.empty_fields:
            summary += f", vacias={item.empty_fields}"
        if item.trailing_space_fields:
            summary += f", espacios={item.trailing_space_fields}"
        if item.warnings:
            summary += f", warnings={item.warnings}"
        print(summary)
        for sample in item.sample_errors or []:
            print(f"  {sample}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
