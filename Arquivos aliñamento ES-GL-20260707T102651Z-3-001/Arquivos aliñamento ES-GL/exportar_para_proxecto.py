from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from alignment_archive import analyze_archive


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Exporta el lote de alineamiento al formato TSV que consumen las interfaces del proyecto."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Carpeta donde están los archivos descargados.",
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "web-angular" / "src" / "assets" / "data",
        help="Destino de verbos_relacionados.tsv y alineaciones_completas.tsv.",
    )
    parser.add_argument(
        "--alignment-file",
        choices=["cba_ES-GL.txt", "cba_pro_ES-GL.txt", "cba_ts_ES-GL.txt", "cba_ts_pro_ES-GL.txt"],
        default="cba_ES-GL.txt",
        help="Archivo de alineaciones a exportar.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Permite exportar aunque la validación detecte problemas.",
    )
    parser.add_argument(
        "--ignore-log-warnings",
        action="store_true",
        help="Permite exportar si el único problema restante son los avisos de los logs.",
    )
    args = parser.parse_args()

    report = analyze_archive(args.root, include_log_warnings=not args.ignore_log_warnings)
    if report.status != "bien" and not args.force:
        print("La validación ha marcado el lote como MAL. Usa --force si igualmente quieres exportarlo.")
        for reason in report.reasons:
            print(f"- {reason}")
        return 1

    args.target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(args.root / "verbos-es-gl.txt", args.target_dir / "verbos_relacionados.tsv")
    shutil.copy2(args.root / args.alignment_file, args.target_dir / "alineaciones_completas.tsv")

    print(f"Exportado verbos_relacionados.tsv desde {args.root / 'verbos-es-gl.txt'}")
    print(f"Exportado alineaciones_completas.tsv desde {args.root / args.alignment_file}")
    print(f"Destino: {args.target_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
