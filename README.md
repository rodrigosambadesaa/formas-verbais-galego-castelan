# Relacion Formas Verbais Galego-Castelan

Script para xerar un corpus aliñado de formas verbais entre castelán (ES) e galego (GL), incluíndo tempos simples e compostos.

## Contexto do traballo

Esta tarefa foi asignada ao autor durante o seu contrato no Proxecto Nos (abril de 2022 a abril de 2023) e non chegou a ser finalizada nese período.

Segundo indicación do autor deste repositorio, o traballo foi rematado por Ainhoa Vivel Couso.

Este repositorio presenta outra forma de implementación do mesmo obxectivo e engade unha interface web en Angular para facilitar a navegación dos verbos relacionados.

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

## Interface web (Angular)

Creouse unha interface web moderna e responsive en tons azuis dentro de `web-angular/` para navegar pares ES-GL e consultar formas aliñadas.

### Execución local (sen Docker)

```powershell
cd .\web-angular
npm install
npm start
```

Logo abre: `http://localhost:4200`

### Execución con Docker

Desde o raíz do proxecto:

```powershell
docker compose up --build
```

Logo abre: `http://localhost:8080`

O servizo inclúe un `healthcheck` HTTP para validar que Nginx está servindo a aplicación estática correctamente. Para
comprobar o estado:

```powershell
docker compose ps
```

## Interface web alternativa (Flutter)

Engadiuse tamén unha interface Flutter Web en `web-flutter/` para consultar os pares de infinitivos ES-GL cunha
experiencia independente da implementación Angular.

### Execución local

```powershell
cd .\web-flutter
flutter pub get
flutter run -d chrome
```

### Execución con Docker

Desde o raíz do proxecto:

```powershell
docker compose up --build web-flutter
```

Logo abre: `http://localhost:8081`

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
