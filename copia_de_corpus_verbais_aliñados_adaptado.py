#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

try:
    import pytz
except ImportError:  # pragma: no cover
    pytz = None

MANUAL_VERIFIED_GL_TO_ES = {
    "abafallar": ["despreciar"],
    "abanar": ["abanicar"],
    "acorrer": ["socorrer"],
}


CONFLICT_VERB_ADDITIONS_ES = [
    "achatarrar",
    "aguijonar",
    "enfrontar",
    "judicializar",
    "reinvertir",
    "territorializar",
    "retroalimentar",
    "patrimonializar",
    "mastectomizar",
    "interrelacionar",
    "renegociar",
    "priorizar",
    "reorientar",
    "reordenar",
    "acartonar",
    "abducir",
    "abotagar",
    "aburguesar",
    "acarretar",
    "emendar",
]

CONFLICT_VERB_ADDITIONS_GL = [
    "xestar",
    "priorizar",
    "reutilizar",
    "xudicializar",
    "subxacer",
    "mutar",
    "rendibilizar",
    "protagonizar",
    "impactar",
    "peonalizar",
]

CONFLICT_VERB_CORRECTIONS_GL = ["argüír", "minguar"]

PERSON_CODES = {
    "Eu": "1PS",
    "Ti": "2PS",
    "El(a)/Vostede": "3PS",
    "Nós": "1PP",
    "Vós": "2PP",
    "Eles(as)/Vostedes": "3PP",
    "Infinitivo": "Inf",
    "Xerundio": "Xer",
    "Participio": "Par",
    "Yo": "1PS",
    "Tú": "2PS",
    "Él/Ella/Usted": "3PS",
    "Nosotros": "1PP",
    "Vosotros": "2PP",
    "Ellos(as)/Ustedes": "3PP",
    "Gerundio": "Ger",
}

SIMPLE_TENSES_FOR_TS = [
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
    ("FN", "IP"),
]

SIMPLE_TENSES_FOR_FULL = [
    ("PI", "PI"),
    ("II", "II"),
    ("EI", "EI"),
    ("FI", "FI"),
    ("TI", "TI"),
    ("PPI", "EI"),
    ("IPI", "MI"),
    ("EPI", "EI"),
    ("PS", "PS"),
    ("IS", "IS"),
    ("FS", "FS"),
    ("IA", "IA"),
    ("IN", "IN"),
    ("FN", "FN"),
    ("FN", "IP"),
]

COMPOUND_TENSES = [
    ("FPI", "FI"),
    ("TPI", "TI"),
    ("PPS", "PS"),
    ("IPS", "IS"),
    ("FPS", "FS"),
    ("FNC", "FN"),
]

PERSON_PAIRS = [
    ("Yo", "Eu"),
    ("Tú", "Ti"),
    ("Él/Ella/Usted", "El(a)/Vostede"),
    ("Nosotros", "Nós"),
    ("Vosotros", "Vós"),
    ("Ellos(as)/Ustedes", "Eles(as)/Vostedes"),
    ("Infinitivo", "Infinitivo"),
    ("Gerundio", "Xerundio"),
    ("Participio", "Participio"),
    ("Infinitivo", "Eu"),
    ("Infinitivo", "Ti"),
    ("Infinitivo", "El(a)/Vostede"),
    ("Infinitivo", "Nós"),
    ("Infinitivo", "Vós"),
    ("Infinitivo", "Eles(as)/Vostedes"),
]

COMPOUND_PERSON_PAIRS = [
    ("Yo", "Eu"),
    ("Tú", "Ti"),
    ("Él/Ella/Usted", "El(a)/Vostede"),
    ("Nosotros", "Nós"),
    ("Vosotros", "Vós"),
    ("Ellos(as)/Ustedes", "Eles(as)/Vostedes"),
    ("Infinitivo", "Infinitivo"),
    ("Gerundio", "Xerundio"),
]


@dataclass
class AlignmentSummary:
    pairs_total: int
    pairs_clean: int
    conflict_rows: int
    listaverbos_size: int
    simple_full_base_rows: int
    compound_rows: int
    simple_rows: int
    simple_pro_rows: int
    full_rows: int
    full_pro_rows: int


@dataclass
class GlOnlyCoverage:
    lemma: str
    status: str
    detail: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Adaptación ejecutable del notebook 'Corpus verbais aliñados'."
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path.cwd(),
        help="Carpeta con los archivos del corpus o del lote exportado.",
    )
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Reutiliza con_vbal*.txt existentes en vez de regenerarlos.",
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        help="Guarda un resumen JSON con métricas del proceso.",
    )
    parser.add_argument(
        "--lista-verbos-gl",
        type=Path,
        help="Lista auxiliar de lemas gallegos para ampliar pares ES-GL con respaldo bilingue.",
    )
    parser.add_argument(
        "--gl-coverage-report",
        type=Path,
        help="Informe de cobertura para listaVerbos frente a pares ES-GL ampliados.",
    )
    return parser.parse_args()


def load_literal_dicts(path: Path) -> list[dict]:
    items: list[dict] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        items.append(ast.literal_eval(line))
    return items


def write_literal_dicts(path: Path, items: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for item in items:
            handle.write(repr(item) + "\n")


def write_lines(path: Path, lines: Iterable[str]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            handle.write(line + "\n")


def load_word_list(path: Path) -> list[str]:
    seen = set()
    items: list[str] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        word = raw_line.strip()
        if not word or word in seen:
            continue
        seen.add(word)
        items.append(word)
    return items


def extract_apertium_gl_to_es_map(dix_path: Path) -> dict[str, list[str]]:
    root = ET.parse(dix_path).getroot()
    result: dict[str, list[str]] = {}
    for entry in root.findall(".//e"):
        senses = [s.attrib.get("n", "").lower() for s in entry.findall(".//s")]
        if not any("vb" in sense or "verb" in sense for sense in senses):
            continue
        p = entry.find("p")
        if p is None:
            continue
        l = p.find("l")
        r = p.find("r")
        if l is None or r is None:
            continue
        es = " ".join("".join(l.itertext()).split()).strip()
        gl = " ".join("".join(r.itertext()).split()).strip()
        if not es or not gl or " " in es or " " in gl:
            continue
        bucket = result.setdefault(gl, [])
        if es not in bucket:
            bucket.append(es)
    return result


def detect_conflicts(conjugations: Iterable[dict]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for item in conjugations:
        conjugation = item.get("conjugations", [{}])[0].get("conjugation", [])
        if int(item.get("known", 1)) == 0:
            rows.append((item["verb"], item["lang"], "V"))
        elif not conjugation or conjugation[0].get("tense") == "None":
            rows.append((item["verb"], item["lang"], "NV"))
    return rows


def augment_pairs_from_lista(
    clean_es: list[dict],
    clean_gl: list[dict],
    lista_words: list[str],
    dix_path: Path,
) -> tuple[list[tuple[str, str]], list[GlOnlyCoverage]]:
    existing_pairs = {(es_item["verb"], gl_item["verb"]) for es_item, gl_item in zip(clean_es, clean_gl)}
    paired_gl = {gl for _, gl in existing_pairs}
    gl_to_es = extract_apertium_gl_to_es_map(dix_path)
    extra_pairs: list[tuple[str, str]] = []
    coverage: list[GlOnlyCoverage] = []

    for gl in lista_words:
        if gl in paired_gl:
            coverage.append(GlOnlyCoverage(lemma=gl, status="already_paired", detail="ya estaba en el corpus"))
            continue
        es_candidates = list(gl_to_es.get(gl, []))
        source = "apertium"
        if not es_candidates and gl in MANUAL_VERIFIED_GL_TO_ES:
            es_candidates = MANUAL_VERIFIED_GL_TO_ES[gl]
            source = "manual_verified"
        if not es_candidates:
            coverage.append(GlOnlyCoverage(lemma=gl, status="unresolved", detail="sin equivalente ES seguro"))
            continue
        added = 0
        for es in es_candidates:
            key = (es, gl)
            if key in existing_pairs:
                continue
            existing_pairs.add(key)
            extra_pairs.append(key)
            added += 1
        if added:
            coverage.append(GlOnlyCoverage(lemma=gl, status="added", detail=f"{source}:{','.join(es_candidates)}"))
        else:
            coverage.append(GlOnlyCoverage(lemma=gl, status="already_paired", detail="equivalente ya presente"))
    return extra_pairs, coverage


def is_reflexive(word: str) -> bool:
    return word.endswith("se")


def build_lista_verbos(conflicts: list[tuple[str, str, str]]) -> list[str]:
    conflict_verbs = {(verb, lang, kind) for verb, lang, kind in conflicts}
    verbs_only = {(verb, lang) for verb, lang, kind in conflict_verbs if kind == "V"}
    additions = {verb for verb, lang in verbs_only if not is_reflexive(verb)}
    additions.update(CONFLICT_VERB_ADDITIONS_GL)
    additions.update(CONFLICT_VERB_CORRECTIONS_GL)
    return sorted(additions)


def split_by_lang(conjugations: list[dict]) -> tuple[list[dict], list[dict]]:
    es_items: list[dict] = []
    gl_items: list[dict] = []
    for item in conjugations:
        if item.get("lang") == "es":
            es_items.append(item)
        elif item.get("lang") == "gl":
            gl_items.append(item)
    return es_items, gl_items


def filter_conflicts(
    es_items: list[dict],
    gl_items: list[dict],
    conflicts: list[tuple[str, str, str]],
) -> tuple[list[dict], list[dict]]:
    conflict_es = {verb for verb, lang, kind in conflicts if lang == "es" and kind == "V"}
    conflict_gl = {verb for verb, lang, kind in conflicts if lang == "gl" and kind == "V"}

    clean_es: list[dict] = []
    clean_gl: list[dict] = []
    for es_item, gl_item in zip(es_items, gl_items):
        if es_item["verb"] in conflict_es or gl_item["verb"] in conflict_gl:
            continue
        clean_es.append(es_item)
        clean_gl.append(gl_item)
    return clean_es, clean_gl


def get_header(now: datetime) -> str:
    return "\n".join(
        [
            "####-----------------------------####",
            f"## LOG ALIÑAMENTO ES-GL ({now.strftime('%H:%M:%S')}) ##",
            "####-----------------------------####",
            "",
        ]
    )


def code(person: str) -> str:
    return PERSON_CODES.get(person, "NA")


def index_by_tense(item: dict) -> dict[str, dict]:
    return {
        tense["code_tense"]: tense
        for tense in item.get("conjugations", [{}])[0].get("conjugation", [])
        if "code_tense" in tense
    }


def people_index(tense: dict) -> dict[str, str]:
    result: dict[str, str] = {}
    for person_info in tense.get("verbal_form", []):
        result[person_info["person"]] = person_info["form"]
    return result


def split_forms(value: str) -> list[str]:
    return [piece.strip() for piece in value.split("/") if piece.strip()]


def align_simple(
    es_items: list[dict],
    gl_items: list[dict],
    tense_pairs: list[tuple[str, str]],
    *,
    special_fn_ip_label: bool,
) -> tuple[list[str], list[str]]:
    rows: list[str] = []
    logs: list[str] = []

    for es_item, gl_item in zip(es_items, gl_items):
        es_tenses = index_by_tense(es_item)
        gl_tenses = index_by_tense(gl_item)

        for tense_es, tense_gl in tense_pairs:
            es_tense = es_tenses.get(tense_es)
            gl_tense = gl_tenses.get(tense_gl)
            if es_tense is None or gl_tense is None:
                logs.append(
                    f"[!] Non hai persoa para o par {es_item['verb']}/{gl_item['verb']} ({tense_es}-{tense_gl})"
                )
                continue

            es_people = people_index(es_tense)
            gl_people = people_index(gl_tense)

            for person_es, person_gl in PERSON_PAIRS:
                try:
                    forms_es = split_forms(es_people[person_es])
                    forms_gl = split_forms(gl_people[person_gl])
                except KeyError:
                    needs_log = (
                        (code(person_es) not in {"Inf", "Ger", "Par"} and tense_es not in {"FN", "IA", "IN"})
                        or (
                            code(person_es) in {"Inf", "Ger", "Par"}
                            and code(person_gl) in {"Inf", "Ger", "Par"}
                            and tense_es == "FN"
                            and tense_gl == "FN"
                        )
                        or (code(person_es) in {"2PS", "1PP", "2PP"} and tense_es == "IN")
                        or (code(person_es) in {"2PS", "2PP"} and tense_es == "IA")
                    )
                    if needs_log:
                        label = "FN(Inf)-IP" if (tense_es, tense_gl) == ("FN", "IP") else f"{tense_es}-{tense_gl}"
                        logs.append(
                            f"[!] Falta o tempo verbal {label}+{code(person_gl)} para o par {es_item['verb']}/{gl_item['verb']}"
                        )
                    continue

                label = (
                    "FN(Inf)-IP"
                    if special_fn_ip_label and (tense_es, tense_gl) == ("FN", "IP")
                    else f"{tense_es}-{tense_gl}"
                )
                for form_es in forms_es:
                    for form_gl in forms_gl:
                        rows.append(f"{form_es}\t{form_gl}\t{label}\t{code(person_gl)}")

    return rows, logs


def align_compound(
    es_items: list[dict],
    gl_items: list[dict],
    ter_item: dict,
    *,
    notebook_effective_behavior: bool,
) -> tuple[list[str], list[str]]:
    rows: list[str] = []
    logs: list[str] = []
    ter_tenses = index_by_tense(ter_item)

    for es_item, gl_item in zip(es_items, gl_items):
        es_tenses = index_by_tense(es_item)
        gl_tenses = index_by_tense(gl_item)
        fn_gl = gl_tenses.get("FN")
        if fn_gl is None:
            logs.append(f"[!] Non hai persoa para o par {es_item['verb']}/{gl_item['verb']} (FN)")
            continue

        gl_people_fn = people_index(fn_gl)
        participles = split_forms(gl_people_fn.get("Participio", ""))
        if not participles:
            logs.append(f"[!] Falta o participio para o par {es_item['verb']}/{gl_item['verb']}")
            continue

        tense_pairs = COMPOUND_TENSES[-1:] if notebook_effective_behavior else COMPOUND_TENSES
        for tense_es, tense_gl_aux in tense_pairs:
            es_tense = es_tenses.get(tense_es)
            ter_tense = ter_tenses.get(tense_gl_aux)
            if es_tense is None or ter_tense is None:
                logs.append(
                    f"[!] Non hai persoa para o par {es_item['verb']}/{gl_item['verb']} ({tense_es}-{tense_gl_aux})"
                )
                continue

            es_people = people_index(es_tense)
            ter_people = people_index(ter_tense)

            for person_es, person_gl in COMPOUND_PERSON_PAIRS:
                try:
                    raw_es = es_people[person_es]
                    forms_es = raw_es.split("/")
                    forms_aux = split_forms(ter_people[person_gl])
                except KeyError:
                    if code(person_es) == "Inf" and code(person_gl) != "Inf":
                        logs.append(
                            f"[!] Falta o tempo verbal {tense_es}-{tense_gl_aux}+{code(person_gl)} para o par {es_item['verb']}/{gl_item['verb']}"
                        )
                    continue

                es_suffix = ""
                if len(forms_es) > 1:
                    try:
                        forms_es[1], es_suffix = forms_es[1].split(" ", 1)
                    except ValueError:
                        logs.append(
                            f"[!] Falta o tempo verbal {tense_es}-{tense_gl_aux}+{code(person_gl)} para o par {es_item['verb']}/{gl_item['verb']}"
                        )
                        continue

                for form_es in forms_es:
                    for aux_gl in forms_aux:
                        for part_gl in participles:
                            left = f"{form_es} {es_suffix}".strip()
                            rows.append(f"{left}\t{aux_gl} {part_gl}\t{tense_es}-{tense_gl_aux}\t{code(person_gl)}")

    return rows, logs


def align_infinitivo_conxugado_only(es_items: list[dict], gl_items: list[dict]) -> tuple[list[str], list[str]]:
    rows: list[str] = []
    logs: list[str] = []
    target_people = [
        "Eu",
        "Ti",
        "El(a)/Vostede",
        "Nós",
        "Vós",
        "Eles(as)/Vostedes",
    ]

    for es_item, gl_item in zip(es_items, gl_items):
        es_tenses = index_by_tense(es_item)
        gl_tenses = index_by_tense(gl_item)
        es_tense = es_tenses.get("FN")
        gl_tense = gl_tenses.get("IP")
        if es_tense is None or gl_tense is None:
            logs.append(f"[!] Non hai persoa para o par {es_item['verb']}/{gl_item['verb']} (FN(Inf)-IP)")
            continue

        es_people = people_index(es_tense)
        gl_people = people_index(gl_tense)
        for person_gl in target_people:
            try:
                forms_es = split_forms(es_people["Infinitivo"])
                forms_gl = split_forms(gl_people[person_gl])
            except KeyError:
                logs.append(
                    f"[!] Falta o tempo verbal FN(Inf)-IP+{code(person_gl)} para o par {es_item['verb']}/{gl_item['verb']}"
                )
                continue

            for form_es in forms_es:
                for form_gl in forms_gl:
                    rows.append(f"{form_es}\t{form_gl}\tFN(Inf)-IP\t{code(person_gl)}")

    return rows, logs


def dedupe_keep_one(rows: list[str]) -> list[str]:
    counter = Counter(rows)
    unique_sorted = sorted(counter)
    return unique_sorted


def dedupe_unique_only(rows: list[str]) -> list[str]:
    counter = Counter(rows)
    return sorted(row for row, count in counter.items() if count == 1)


def now_madrid() -> datetime:
    if pytz is None:
        return datetime.now()
    return datetime.now(pytz.timezone("Europe/Madrid"))


def load_json_from_linguakit(path: Path) -> dict:
    items = load_literal_dicts(path)
    if not items:
        raise ValueError(f"No hay datos en {path}")
    return items[0]


def conjugate_ter_gl(repo_root: Path) -> dict:
    bat_path = repo_root / "Linguakit" / "linguakit.bat"
    if not bat_path.exists():
        raise FileNotFoundError("No se encontró Linguakit/linguakit.bat para conjugar 'ter'.")
    proc = subprocess.run(
        [str(bat_path), "conj", "gl"],
        input="ter",
        text=True,
        capture_output=True,
        check=True,
        cwd=str(repo_root),
    )
    return json.loads(proc.stdout)


def conjugate_gl_verb(repo_root: Path, verb: str) -> dict:
    bat_path = repo_root / "Linguakit" / "linguakit.bat"
    if not bat_path.exists():
        raise FileNotFoundError(f"No se encontró Linguakit/linguakit.bat para conjugar '{verb}'.")
    proc = subprocess.run(
        [str(bat_path), "conj", "gl"],
        input=verb,
        text=True,
        capture_output=True,
        check=True,
        cwd=str(repo_root),
    )
    return json.loads(proc.stdout)


def conjugate_es_verb(repo_root: Path, verb: str) -> dict:
    bat_path = repo_root / "Linguakit" / "linguakit.bat"
    if not bat_path.exists():
        raise FileNotFoundError(f"No se encontró Linguakit/linguakit.bat para conjugar '{verb}'.")
    proc = subprocess.run(
        [str(bat_path), "conj", "es"],
        input=verb,
        text=True,
        capture_output=True,
        check=True,
        cwd=str(repo_root),
    )
    return json.loads(proc.stdout)


def is_conjugated_verb(conj_json: dict) -> bool:
    if int(conj_json.get("known", 1)) == 0:
        return False
    conjugations = conj_json.get("conjugations", [])
    if not conjugations:
        return False
    blocks = conjugations[0].get("conjugation", [])
    if not blocks:
        return False
    first_tense = str(blocks[0].get("tense", "")).strip()
    return first_tense and first_tense != "None"


def run(args: argparse.Namespace) -> AlignmentSummary:
    workdir = args.workdir.resolve()
    con_vbal = workdir / "con_vbal.txt"
    con_vbal_es = workdir / "con_vbal_es.txt"
    con_vbal_gl = workdir / "con_vbal_gl.txt"
    con_vbal_def_es = workdir / "con_vbal_def_es.txt"
    con_vbal_def_gl = workdir / "con_vbal_def_gl.txt"
    pal_conf = workdir / "pal_conf.txt"
    lista_verbos_detectados = workdir / "listaVerbos.detectados.txt"
    cba_ts = workdir / "cba_ts_ES-GL.txt"
    cba_ts_log = workdir / "cba_ts_log.txt"
    cba_ts_pro = workdir / "cba_ts_pro_ES-GL.txt"
    cba_full = workdir / "cba_ES-GL.txt"
    cba_full_log = workdir / "cba_log.txt"
    cba_full_pro = workdir / "cba_pro_ES-GL.txt"
    gl_coverage_report = args.gl_coverage_report or (workdir / "verbos_gl_cobertura.tsv")

    conjugations = load_literal_dicts(con_vbal)
    conflicts = detect_conflicts(conjugations)
    write_lines(pal_conf, [f"{verb}\t{lang}\t{kind}" for verb, lang, kind in conflicts])

    lista = build_lista_verbos(conflicts)
    write_lines(lista_verbos_detectados, lista)

    es_items, gl_items = split_by_lang(conjugations)
    write_literal_dicts(con_vbal_es, es_items)
    write_literal_dicts(con_vbal_gl, gl_items)

    clean_es, clean_gl = filter_conflicts(es_items, gl_items, conflicts)
    write_literal_dicts(con_vbal_def_es, clean_es)
    write_literal_dicts(con_vbal_def_gl, clean_gl)

    simple_rows, simple_log_rows = align_simple(
        clean_es,
        clean_gl,
        SIMPLE_TENSES_FOR_TS,
        special_fn_ip_label=True,
    )
    simple_pro_rows = dedupe_unique_only(simple_rows)
    write_lines(cba_ts, simple_rows)
    write_lines(cba_ts_pro, simple_pro_rows)
    write_lines(cba_ts_log, [get_header(now_madrid())] + simple_log_rows)

    ter_candidates = [item for item in gl_items if item.get("verb") == "ter"]
    ter_item = ter_candidates[0] if ter_candidates else conjugate_ter_gl(Path(__file__).resolve().parent)

    simple_full_rows, simple_full_log_rows = align_simple(
        clean_es,
        clean_gl,
        SIMPLE_TENSES_FOR_FULL,
        special_fn_ip_label=False,
    )
    inf_conj_rows, inf_conj_logs = align_infinitivo_conxugado_only(clean_es, clean_gl)
    compound_rows, compound_log_rows = align_compound(
        clean_es,
        clean_gl,
        ter_item,
        notebook_effective_behavior=True,
    )
    full_rows = simple_full_rows + inf_conj_rows + compound_rows
    full_log_lines = [get_header(now_madrid())] + simple_full_log_rows + inf_conj_logs + compound_log_rows

    if args.lista_verbos_gl and args.lista_verbos_gl.exists():
        lista_words = load_word_list(args.lista_verbos_gl)
        extra_pairs, gl_coverage = augment_pairs_from_lista(
            clean_es,
            clean_gl,
            lista_words,
            Path(__file__).resolve().parent / "apertium-spa-glg" / "apertium-spa-glg.spa-glg.dix",
        )
        repo_root = Path(__file__).resolve().parent
        for es_lemma, gl_lemma in extra_pairs:
            try:
                es_conj = conjugate_es_verb(repo_root, es_lemma)
                gl_conj = conjugate_gl_verb(repo_root, gl_lemma)
            except Exception as exc:
                full_log_lines.append(f"[!] Error de conjugacion para {es_lemma}/{gl_lemma}: {exc}")
                continue
            if not is_conjugated_verb(es_conj) or not is_conjugated_verb(gl_conj):
                full_log_lines.append(f"[!] Verbo desconocido o sin conjugacion: {es_lemma}/{gl_lemma}")
                continue
            extra_simple_rows, extra_simple_logs = align_simple(
                [es_conj],
                [gl_conj],
                SIMPLE_TENSES_FOR_FULL,
                special_fn_ip_label=False,
            )
            extra_inf_rows, extra_inf_logs = align_infinitivo_conxugado_only([es_conj], [gl_conj])
            extra_comp_rows, extra_comp_logs = align_compound(
                [es_conj],
                [gl_conj],
                ter_item,
                notebook_effective_behavior=True,
            )
            full_rows.extend(extra_simple_rows + extra_inf_rows + extra_comp_rows)
            full_log_lines.extend(extra_simple_logs + extra_inf_logs + extra_comp_logs)

        write_lines(
            gl_coverage_report,
            ["lemma\tstatus\tdetail"]
            + [f"{item.lemma}\t{item.status}\t{item.detail}" for item in gl_coverage],
        )

    full_pro_rows = dedupe_unique_only(full_rows)
    write_lines(cba_full, full_rows)
    write_lines(cba_full_pro, full_pro_rows)
    write_lines(cba_full_log, full_log_lines)

    summary = AlignmentSummary(
        pairs_total=min(len(es_items), len(gl_items)),
        pairs_clean=min(len(clean_es), len(clean_gl)),
        conflict_rows=len(conflicts),
        listaverbos_size=len(lista),
        simple_full_base_rows=len(simple_full_rows),
        compound_rows=len(compound_rows),
        simple_rows=len(simple_rows),
        simple_pro_rows=len(simple_pro_rows),
        full_rows=len(full_rows),
        full_pro_rows=len(full_pro_rows),
    )
    if args.summary_json:
        args.summary_json.write_text(json.dumps(summary.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(json.dumps(summary.__dict__, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
