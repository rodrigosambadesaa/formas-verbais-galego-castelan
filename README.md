# Relacion Formas Verbais Galego-Castelan

Script para xerar un corpus aliñado de formas verbais entre castelán (ES) e galego (GL), incluíndo tempos simples e compostos.

## Que fai

- Le pares de infinitivos ES-GL desde un TSV ou desde un dicionario bilingue de Apertium.
- Conxuga cada verbo en ES e GL mediante LinguaKit.
- Aliña as formas por tempo/persoa.
- Xera un ficheiro TXT final listo para explotación lingüística.

## Requisitos

- Python 3.10+
- Perl (recomendado Strawberry Perl en Windows)
- Git

## Instalación rápida (Windows)

```powershell
git clone https://github.com/citiususc/Linguakit.git
git clone https://github.com/apertium/apertium-spa-glg.git
```

Instalar módulos Perl necesarios:

```powershell
cpanm PerlIO::gzip LWP::UserAgent HTTP::Request::Common LWP::Protocol::https
```

## Uso

### 1) Modo TSV (pares propios)

Entrada esperada: `verbos-es-gl.txt` con formato:

```text
verbo_es<TAB>verbo_gl<TAB>V
```

Ejecución:

```powershell
python .\copia_de_corpus_verbais_aliñados.py \
  --input .\verbos-es-gl.txt \
  --output .\formas_verbais_es_gl.txt \
  --log .\formas_verbais_es_gl.log \
  --linguakit .\Linguakit\linguakit.bat
```

### 2) Modo completo (Apertium)

```powershell
python .\copia_de_corpus_verbais_aliñados.py \
  --pair-source apertium \
  --apertium-dix .\apertium-spa-glg\apertium-spa-glg.spa-glg.dix \
  --export-pairs .\verbos-es-gl-completo.txt \
  --output .\formas_verbais_es_gl_completo.txt \
  --log .\formas_verbais_es_gl_completo.log \
  --linguakit .\Linguakit\linguakit.bat \
  --conj-timeout 8 \
  --workers 12
```

## Que se sobe a GitHub

Este repositorio está preparado para subir:

- Código fonte do proxecto.
- Documentación.

E NON sobe:

- Repositorios externos clonados (`Linguakit/`, `apertium-spa-glg/`).
- Saídas xeradas (`formas_verbais_*.txt`, `*.log`).
- Cachés locais e ficheiros temporais.

## Atribución de fontes

Este proxecto usa recursos de terceiros. Consulta [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) para detalle de autoría e ligazóns oficiais.

## Nota de licenza

Antes de distribuír saídas xeradas a gran escala, revisa e cumpre as licenzas dos recursos externos empregados (LinguaKit e Apertium), xa que este repositorio non os vendeiriza.
