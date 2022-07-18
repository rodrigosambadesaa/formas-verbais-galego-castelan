from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from alignment_archive import EXPECTED_FILES, clean_tabular_file, iter_expected_tabular_files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Limpia los archivos tabulares del lote, recorta espacios y separa filas inválidas."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Carpeta original del lote.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "Arquivos aliñamento ES-GL-limpo",
        help="Carpeta donde se escribirán los archivos saneados.",
    )
    args = parser.parse_args()

    root = args.root
    output_dir = args.output_dir
    rejected_dir = output_dir / "_rexeitados"
    output_dir.mkdir(parents=True, exist_ok=True)
    rejected_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for name, expected_columns in iter_expected_tabular_files():
        source = root / name
        if not source.exists():
            continue
        result = clean_tabular_file(
            source=source,
            destination=output_dir / name,
            rejected=rejected_dir / f"{source.stem}.rexeitados.tsv",
            expected_columns=expected_columns,
        )
        results.append(result)

    for name, expected_columns in EXPECTED_FILES.items():
        if expected_columns is not None:
            continue
        source = root / name
        if not source.exists():
            continue
        shutil.copy2(source, output_dir / name)

    summary_path = output_dir / "limpeza_resumo.json"
    summary_payload = {
        "source_root": str(root),
        "output_root": str(output_dir),
        "files": [json.loads(result.to_json()) for result in results],
    }
    summary_path.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Limpieza completada en: {output_dir}")
    for result in results:
        print(
            f"- {Path(result.source).name}: limpias={result.written_rows}, rechazadas={result.rejected_rows}"
        )
    print(f"Resumen JSON: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
