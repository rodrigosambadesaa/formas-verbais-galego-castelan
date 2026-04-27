#!/usr/bin/env python3
"""
Alinea formas verbales entre castellano y galego usando LinguaKit.

Entrada esperada (TSV):
  verbos-es-gl.txt
con columnas:
  1) infinitivo es
  2) infinitivo gl
  3) tipo (opcional, no se usa)

Salida:
  - TXT con alineaciones: ES<TAB>GL<TAB>TENSE<TAB>PERSON_CODE
  - LOG con incidencias
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


DEFAULT_INPUT = "verbos-es-gl.txt"
DEFAULT_OUTPUT = "formas_verbais_es_gl.txt"
DEFAULT_LOG = "formas_verbais_es_gl.log"
DEFAULT_LINGUAKIT = str(Path("Linguakit") / "linguakit.bat")
DEFAULT_APERTIUM_DIX = str(Path("apertium-spa-glg") / "apertium-spa-glg.spa-glg.dix")


FINITE_PERSON_PAIRS = [
    ("Yo", "Eu"),
    ("Tu", "Ti"),
    ("El/Ella/Usted", "El(a)/Vostede"),
    ("Nosotros", "Nos"),
    ("Vosotros", "Vos"),
    ("Ellos(as)/Ustedes", "Eles(as)/Vostedes"),
]

NOMINAL_PERSON_PAIRS = [
    ("Infinitivo", "Infinitivo"),
    ("Gerundio", "Xerundio"),
    ("Participio", "Participio"),
]

INFINITIVO_CONXUGADO_PAIRS = [
    ("Infinitivo", "Eu"),
    ("Infinitivo", "Ti"),
    ("Infinitivo", "El(a)/Vostede"),
    ("Infinitivo", "Nos"),
    ("Infinitivo", "Vos"),
    ("Infinitivo", "Eles(as)/Vostedes"),
]

SIMPLE_TENSE_PAIRS = [
    ("PI", "PI"),
    ("II", "II"),
    ("EI", "EI"),
    ("FI", "FI"),
    ("TI", "TI"),
    ("PS", "PS"),
    ("IS", "IS"),
    ("FS", "FS"),
    ("IA", "IA"),
    ("IN", "IN"),
    ("FN", "FN"),
]

# Tiempos compuestos ES -> tiempo del auxiliar "ter" en GL.
COMPOUND_TENSE_PAIRS = [
    ("PPI", "EI"),
    ("IPI", "MI"),
    ("EPI", "EI"),
    ("FPI", "FI"),
    ("TPI", "TI"),
    ("PPS", "PS"),
    ("IPS", "IS"),
    ("FPS", "FS"),
    ("FNC", "FN"),
]

PERSON_CODE = {
    "eu": "1PS",
    "yo": "1PS",
    "ti": "2PS",
    "tu": "2PS",
    "el/ella/usted": "3PS",
    "el(a)/vostede": "3PS",
    "nos": "1PP",
    "nosotros": "1PP",
    "vos": "2PP",
    "vosotros": "2PP",
    "ellos(as)/ustedes": "3PP",
    "eles(as)/vostedes": "3PP",
    "infinitivo": "Inf",
    "gerundio": "Ger",
    "xerundio": "Xer",
    "participio": "Par",
}


@dataclass
class VerbPair:
    es: str
    gl: str


def normalize_text(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    text = text.replace("É", "E").replace("é", "e")
    text = text.replace("Ú", "U").replace("ú", "u")
    text = "".join(
        ch for ch in unicodedata.normalize("NFKD", text) if not unicodedata.combining(ch)
    )
    return text


def canon_person(text: str) -> str:
    return normalize_text(text).lower()


def split_forms(raw_form: str) -> List[str]:
    parts = [p.strip() for p in raw_form.split("/")]
    return [p for p in parts if p]


def decode_output(raw: bytes) -> str:
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def build_subprocess_env() -> Dict[str, str]:
    env = os.environ.copy()
    path_value = env.get("Path", "")
    extras = [
        r"C:\Strawberry\perl\bin",
        r"C:\Strawberry\c\bin",
    ]
    for p in extras:
        if p.lower() not in path_value.lower():
            path_value = f"{p};{path_value}" if path_value else p
    env["Path"] = path_value
    return env


def load_pairs(input_path: Path) -> List[VerbPair]:
    if not input_path.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {input_path}")

    pairs: List[VerbPair] = []
    seen = set()
    with input_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) < 2:
                continue
            es = row[0].strip()
            gl = row[1].strip()
            if not es or not gl:
                continue
            key = (es.lower(), gl.lower())
            if key in seen:
                continue
            seen.add(key)
            pairs.append(VerbPair(es=es, gl=gl))
    return pairs


def flatten_xml_text(elem: ET.Element) -> str:
    text = "".join(elem.itertext())
    return " ".join(text.split()).strip()


def has_verb_tag(elem: ET.Element) -> bool:
    for s in elem.findall(".//s"):
        n = (s.attrib.get("n") or "").lower()
        if "vb" in n or "verb" in n:
            return True
    return False


def extract_apertium_pairs(dix_path: Path) -> List[VerbPair]:
    if not dix_path.exists():
        raise FileNotFoundError(f"No existe el diccionario Apertium: {dix_path}")

    tree = ET.parse(dix_path)
    root = tree.getroot()
    pairs: List[VerbPair] = []
    seen = set()

    def looks_like_infinitive(token: str) -> bool:
        t = canon_person(token)
        return t.endswith(("ar", "er", "ir", "or")) and len(t) >= 3

    for entry in root.findall(".//e"):
        if not has_verb_tag(entry):
            continue

        # Estructura habitual: <e><p><l>...</l><r>...</r></p></e>
        p = entry.find("p")
        if p is None:
            continue
        l = p.find("l")
        r = p.find("r")
        if l is None or r is None:
            continue

        es = flatten_xml_text(l)
        gl = flatten_xml_text(r)
        if not es or not gl:
            continue

        # Evita frases multi-palabra o entradas no verbales de superficie.
        if " " in es or " " in gl:
            continue

        if not looks_like_infinitive(es) or not looks_like_infinitive(gl):
            continue

        key = (es.lower(), gl.lower())
        if key in seen:
            continue
        seen.add(key)
        pairs.append(VerbPair(es=es, gl=gl))

    return pairs


def export_pairs_tsv(path: Path, pairs: Sequence[VerbPair]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        for p in pairs:
            f.write(f"{p.es}\t{p.gl}\tV\n")


def run_linguakit_conj(
    linguakit_cmd: str,
    verb: str,
    lang: str,
    timeout_s: int = 20,
    env: Optional[Dict[str, str]] = None,
) -> Dict:
    cmd = [linguakit_cmd, "conj", lang]
    try:
        proc = subprocess.run(
            cmd,
            input=verb.encode("utf-8"),
            capture_output=True,
            text=False,
            shell=False,
            timeout=timeout_s,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Timeout de LinguaKit para {verb}/{lang} tras {timeout_s}s"
        ) from exc
    if proc.returncode != 0:
        stderr = decode_output(proc.stderr)
        raise RuntimeError(f"LinguaKit devolvio error para {verb}/{lang}: {stderr}")

    stdout = decode_output(proc.stdout).strip()
    if not stdout:
        raise RuntimeError(f"LinguaKit no devolvio salida para {verb}/{lang}")

    return json.loads(stdout)


def build_tense_map(conj_json: Dict) -> Dict[str, Dict[str, object]]:
    result: Dict[str, Dict[str, object]] = {}
    conjugations = conj_json.get("conjugations", [])
    if not conjugations:
        return result
    for block in conjugations[0].get("conjugation", []):
        code = str(block.get("code_tense", "")).strip()
        if not code:
            continue
        result[code] = block
    return result


def build_person_map(tense_block: Dict[str, object]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for item in tense_block.get("verbal_form", []):
        person = canon_person(str(item.get("person", "")))
        form = str(item.get("form", "")).strip()
        if not person or not form:
            continue
        out[person] = form
    return out


def person_code(person_gl: str) -> str:
    return PERSON_CODE.get(canon_person(person_gl), "NA")


def align_simple_pair(
    es_map: Dict[str, Dict[str, object]],
    gl_map: Dict[str, Dict[str, object]],
    tense_es: str,
    tense_gl: str,
    verb_es: str,
    verb_gl: str,
    rows: List[Tuple[str, str, str, str]],
    logs: List[str],
) -> None:
    if tense_es not in es_map or tense_gl not in gl_map:
        logs.append(
            f"[!] Falta tense para {verb_es}/{verb_gl}: {tense_es}-{tense_gl}"
        )
        return

    es_persons = build_person_map(es_map[tense_es])
    gl_persons = build_person_map(gl_map[tense_gl])

    person_pairs: Sequence[Tuple[str, str]]
    if tense_es == "FN" and tense_gl == "FN":
        person_pairs = NOMINAL_PERSON_PAIRS
    else:
        person_pairs = FINITE_PERSON_PAIRS

    for person_es, person_gl in person_pairs:
        p_es = canon_person(person_es)
        p_gl = canon_person(person_gl)
        if p_es not in es_persons or p_gl not in gl_persons:
            continue
        for form_es in split_forms(es_persons[p_es]):
            for form_gl in split_forms(gl_persons[p_gl]):
                rows.append((form_es, form_gl, f"{tense_es}-{tense_gl}", person_code(person_gl)))


def align_infinitivo_conxugado(
    es_map: Dict[str, Dict[str, object]],
    gl_map: Dict[str, Dict[str, object]],
    verb_es: str,
    verb_gl: str,
    rows: List[Tuple[str, str, str, str]],
    logs: List[str],
) -> None:
    if "FN" not in es_map or "IP" not in gl_map:
        logs.append(f"[!] Falta FN/IP para {verb_es}/{verb_gl}")
        return

    es_persons = build_person_map(es_map["FN"])
    gl_persons = build_person_map(gl_map["IP"])

    for person_es, person_gl in INFINITIVO_CONXUGADO_PAIRS:
        p_es = canon_person(person_es)
        p_gl = canon_person(person_gl)
        if p_es not in es_persons or p_gl not in gl_persons:
            continue
        for form_es in split_forms(es_persons[p_es]):
            for form_gl in split_forms(gl_persons[p_gl]):
                rows.append((form_es, form_gl, "FN(Inf)-IP", person_code(person_gl)))


def align_compound_pair(
    es_map: Dict[str, Dict[str, object]],
    gl_map: Dict[str, Dict[str, object]],
    ter_map: Dict[str, Dict[str, object]],
    tense_es: str,
    tense_aux_gl: str,
    verb_es: str,
    verb_gl: str,
    rows: List[Tuple[str, str, str, str]],
    logs: List[str],
) -> None:
    if tense_es not in es_map:
        logs.append(f"[!] Falta tense ES para {verb_es}/{verb_gl}: {tense_es}")
        return
    if tense_aux_gl not in ter_map:
        logs.append(
            f"[!] Falta tense auxiliar GL(ter) para {verb_es}/{verb_gl}: {tense_aux_gl}"
        )
        return
    if "FN" not in gl_map:
        logs.append(f"[!] Falta FN(GL) para participio en {verb_es}/{verb_gl}")
        return

    es_persons = build_person_map(es_map[tense_es])
    aux_persons = build_person_map(ter_map[tense_aux_gl])
    gl_nominal = build_person_map(gl_map["FN"])

    participio_gl = gl_nominal.get(canon_person("Participio"), "")
    if not participio_gl:
        logs.append(f"[!] Falta participio GL para {verb_es}/{verb_gl}")
        return

    if tense_es == "FNC":
        use_pairs = [
            ("Infinitivo", "Infinitivo"),
            ("Gerundio", "Xerundio"),
        ]
    else:
        use_pairs = FINITE_PERSON_PAIRS

    for person_es, person_gl in use_pairs:
        p_es = canon_person(person_es)
        p_gl = canon_person(person_gl)
        if p_es not in es_persons or p_gl not in aux_persons:
            continue
        for form_es in split_forms(es_persons[p_es]):
            for aux_gl in split_forms(aux_persons[p_gl]):
                for part_gl in split_forms(participio_gl):
                    rows.append(
                        (
                            form_es,
                            f"{aux_gl} {part_gl}".strip(),
                            f"{tense_es}-{tense_aux_gl}",
                            person_code(person_gl),
                        )
                    )


def write_outputs(output_path: Path, log_path: Path, rows: List[Tuple[str, str, str, str]], logs: List[str]) -> None:
    # Conserva orden determinista sin duplicados.
    seen = set()
    unique_rows: List[Tuple[str, str, str, str]] = []
    for row in rows:
        if row in seen:
            continue
        seen.add(row)
        unique_rows.append(row)

    with output_path.open("w", encoding="utf-8", newline="") as f:
        for form_es, form_gl, tense, pcode in unique_rows:
            f.write(f"{form_es}\t{form_gl}\t{tense}\t{pcode}\n")

    with log_path.open("w", encoding="utf-8", newline="") as f:
        f.write(f"## LOG ALINEAMENTO ES-GL ({datetime.now().isoformat(timespec='seconds')})\n\n")
        if not logs:
            f.write("Sin incidencias.\n")
        else:
            for line in logs:
                f.write(f"{line}\n")


def resolve_linguakit_cmd(path_arg: str) -> str:
    cmd_path = Path(path_arg)
    if cmd_path.exists():
        return str(cmd_path)

    # Fallbacks comunes por si se pasa solo carpeta.
    if cmd_path.is_dir():
        bat = cmd_path / "linguakit.bat"
        perl = cmd_path / "linguakit"
        if bat.exists():
            return str(bat)
        if perl.exists():
            return str(perl)

    raise FileNotFoundError(
        f"No se encontro el ejecutable de LinguaKit en: {path_arg}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Alinea formas verbales ES-GL con LinguaKit y genera un TXT final."
    )
    parser.add_argument("--input", default=DEFAULT_INPUT, help="TSV de verbos ES-GL")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="TXT de salida")
    parser.add_argument("--log", default=DEFAULT_LOG, help="Archivo log")
    parser.add_argument(
        "--pair-source",
        choices=["tsv", "apertium"],
        default="tsv",
        help="Origen de pares de infinitivos ES-GL",
    )
    parser.add_argument(
        "--apertium-dix",
        default=DEFAULT_APERTIUM_DIX,
        help="Ruta al .dix bilingue spa-glg de Apertium",
    )
    parser.add_argument(
        "--export-pairs",
        default="",
        help="Si se indica, exporta el listado de pares generado a TSV",
    )
    parser.add_argument(
        "--conj-timeout",
        type=int,
        default=20,
        help="Timeout por llamada al conjugador (segundos)",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=250,
        help="Muestra progreso cada N pares",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Numero de workers para preconjugacion paralela",
    )
    parser.add_argument(
        "--linguakit",
        default=DEFAULT_LINGUAKIT,
        help="Ruta a linguakit.bat (Windows) o linguakit (Linux/macOS)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    log_path = Path(args.log)

    try:
        linguakit_cmd = resolve_linguakit_cmd(args.linguakit)
        if args.pair_source == "tsv":
            pairs = load_pairs(input_path)
        else:
            pairs = extract_apertium_pairs(Path(args.apertium_dix))
            if args.export_pairs:
                export_pairs_tsv(Path(args.export_pairs), pairs)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    rows: List[Tuple[str, str, str, str]] = []
    logs: List[str] = []
    sub_env = build_subprocess_env()

    conj_cache: Dict[Tuple[str, str], Dict] = {}

    # Preconjuga en paralelo para reducir drásticamente el tiempo total.
    unique_tasks: List[Tuple[str, str]] = []
    seen_tasks = set()
    for p in pairs:
        for lang, verb in (("es", p.es), ("gl", p.gl)):
            k = (verb.lower(), lang)
            if k in seen_tasks:
                continue
            seen_tasks.add(k)
            unique_tasks.append((verb, lang))
    # Necesario para tiempos compuestos.
    if ("ter", "gl") not in seen_tasks:
        unique_tasks.append(("ter", "gl"))

    def _conj_job(verb: str, lang: str) -> Tuple[str, str, Optional[Dict], Optional[str]]:
        try:
            c = run_linguakit_conj(
                linguakit_cmd,
                verb,
                lang,
                timeout_s=args.conj_timeout,
                env=sub_env,
            )
            return verb, lang, c, None
        except Exception as exc:
            return verb, lang, None, str(exc)

    workers = max(1, int(args.workers))
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_conj_job, v, l) for v, l in unique_tasks]
        for fut in as_completed(futs):
            verb, lang, conj, err = fut.result()
            done += 1
            if err:
                logs.append(f"[!] Error de conjugacion para {verb}/{lang}: {err}")
            else:
                conj_cache[(verb.lower(), lang)] = conj
            if args.progress_every > 0 and done % args.progress_every == 0:
                print(f"Preconjugacion: {done}/{len(unique_tasks)}")

    ter_key = ("ter", "gl")
    if ter_key not in conj_cache:
        print("[ERROR] No se pudo conjugar 'ter' en GL", file=sys.stderr)
        write_outputs(output_path, log_path, rows, logs)
        return 1
    ter_map = build_tense_map(conj_cache[ter_key])

    for idx, pair in enumerate(pairs, start=1):
        try:
            es_json = conj_cache[(pair.es.lower(), "es")]
            gl_json = conj_cache[(pair.gl.lower(), "gl")]
        except Exception as exc:
            logs.append(f"[!] Error de conjugacion para {pair.es}/{pair.gl}: {exc}")
            continue

        if int(es_json.get("known", 1)) == 0 or int(gl_json.get("known", 1)) == 0:
            logs.append(f"[!] Verbo desconocido: {pair.es}/{pair.gl}")
            continue

        es_map = build_tense_map(es_json)
        gl_map = build_tense_map(gl_json)

        for tense_es, tense_gl in SIMPLE_TENSE_PAIRS:
            align_simple_pair(
                es_map,
                gl_map,
                tense_es,
                tense_gl,
                pair.es,
                pair.gl,
                rows,
                logs,
            )

        align_infinitivo_conxugado(es_map, gl_map, pair.es, pair.gl, rows, logs)

        for tense_es, tense_aux_gl in COMPOUND_TENSE_PAIRS:
            align_compound_pair(
                es_map,
                gl_map,
                ter_map,
                tense_es,
                tense_aux_gl,
                pair.es,
                pair.gl,
                rows,
                logs,
            )

        if args.progress_every > 0 and idx % args.progress_every == 0:
            print(
                f"Progreso: {idx}/{len(pairs)} pares | filas={len(rows)} | cache={len(conj_cache)}"
            )

    write_outputs(output_path, log_path, rows, logs)
    print(f"Pares procesados: {len(pairs)}")
    print(f"Conjugaciones en cache: {len(conj_cache)}")
    print(f"OK: {len(rows)} alineaciones generadas (antes de deduplicar)")
    print(f"Salida: {output_path}")
    print(f"Log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
