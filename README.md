# Relacion Formas Verbais Galego-Castelan

Script y clientes visuales para generar y explorar un corpus alineado de formas verbales entre castellano (ES) y gallego (GL), incluyendo tiempos simples y compuestos.

## Contexto del proyecto

Este repositorio nace como un proyecto de desarrollo personal, investigación independiente y autoaprendizaje en el ámbito de las tecnologías del lenguaje. Su objetivo es explorar la alineación morfológica verbal y poner en práctica arquitecturas web modernas mediante el despliegue de cuatro interfaces independientes con funcionalidad equivalente.

Este repositorio incluye cuatro interfaces para consultar el corpus:

- `web-angular/`: cliente Angular.
- `flutter_app/`: cliente Flutter con salida web dockerizada.
- `web-php/`: implementación en PHP puro.
- `web-laravel/`: implementación en Laravel.

## Qué hace el proyecto

- Lee pares de infinitivos ES-GL desde un TSV o desde un diccionario bilingüe de Apertium.
- Conjuga cada verbo en ES y GL mediante LinguaKit.
- Alinea las formas por tiempo y persona.
- Genera un fichero TXT final listo para explotación lingüística.
- Permite navegar el corpus desde cuatro stacks web distintos con una funcionalidad equivalente.

## Requisitos del generador

- Python 3.10+
- Perl (recomendado Strawberry Perl en Windows)
- Git

## Instalación rápida (Windows)

```powershell
git clone https://github.com
git clone https://github.com
```

Instala los módulos Perl necesarios:

```powershell
cpanm PerlIO::gzip LWP::UserAgent HTTP::Request::Common LWP::Protocol::https
```

## Generación del corpus

### 1) Modo TSV (pares propios)

Entrada esperada: `verbos-es-gl.txt` con formato:

```text
verbo_es<TAB>verbo_gl<TAB>V
```

Ejecución:

```powershell
python .\corpus_verbal.py \
  --input .\verbos-es-gl.txt \
  --output .\formas_verbais_es_gl.txt \
  --log .\formas_verbais_es_gl.log \
  --linguakit .\Linguakit\linguakit.bat
```

### 2) Modo completo (Apertium)

```powershell
python .\corpus_verbal.py \
  --pair-source apertium \
  --apertium-dix .\apertium-spa-glg\apertium-spa-glg.spa-glg.dix \
  --export-pairs .\verbos-es-gl-completo.txt \
  --output .\formas_verbais_es_gl_completo.txt \
  --log .\formas_verbais_es_gl_completo.log \
  --linguakit .\Linguakit\linguakit.bat \
  --conj-timeout 8 \
  --workers 12
```

## Interfaces disponibles

### Angular

`web-angular/` ofrece:

- búsqueda global por infinitivos y formas conjugadas,
- filtros por tiempo y persona,
- ordenación de pares y tabla,
- diseño responsive.

Local:

```powershell
cd .\web-angular
npm install
npm start
```

Disponible en `http://localhost:4200`.

Docker:

```powershell
docker compose up --build web-angular
```

Disponible en `http://localhost:28180`.

### Flutter

`flutter_app/` replica la consulta del corpus en Flutter.

Preparación local:

```powershell
cd .\flutter_app
flutter create .
powershell -ExecutionPolicy Bypass -File .\tool\sync_assets.ps1
flutter pub get
flutter run
```

Docker:

```powershell
docker compose up --build web-flutter
```

Disponible en `http://localhost:28181`.

### PHP puro

`web-php/` implementa la misma experiencia sin framework frontend y con renderizado server-side.

Local:

```powershell
cd .\web-php
php -S localhost:8082 -t public
```

Disponible en `http://localhost:8082`.

Docker:

```powershell
docker compose up --build web-php
```

Disponible en `http://localhost:28182`.

### Laravel

`web-laravel/` ofrece la misma funcionalidad montada sobre Laravel.

Local:

```powershell
cd .\web-laravel
php artisan serve --host=127.0.0.1 --port=8083
```

Disponible en `http://127.0.0.1:8083`.

Docker:

```powershell
docker compose up --build web-laravel
```

Disponible en `http://localhost:28183`.

## Docker Compose completo

El `docker-compose.yml` de la raíz levanta las cuatro interfaces:

- `web-angular` en `http://localhost:28180`
- `web-flutter` en `http://localhost:28181`
- `web-php` en `http://localhost:28182`
- `web-laravel` en `http://localhost:28183`

Para arrancarlas juntas:

```powershell
docker compose up --build
```

Para ver estado:

```powershell
docker compose ps
```

Para parar y limpiar contenedores:

```powershell
docker compose down
```

## Datos que usan las interfaces

Las cuatro interfaces consumen estos TSV:

- `verbos_relacionados.tsv`: listado de pares ES-GL.
- `alineaciones_completas.tsv`: formas alineadas por tiempo y persona.

Angular los lee desde `web-angular/src/assets/data/`.
Flutter los sincroniza a `flutter_app/assets/data/` mediante `tool/sync_assets.ps1`.
PHP puro y Laravel los leen desde la carpeta de Angular en desarrollo local y los copian dentro de la imagen cuando se construyen en Docker.

## Qué se sube a GitHub

Este repositorio está preparado para subir:

- código fuente del proyecto,
- documentación,
- clientes Angular, Flutter, PHP puro y Laravel.

Y no sube:

- repositorios externos clonados (`Linguakit/`, `apertium-spa-glg/`),
- salidas generadas (`formas_verbais_*.txt`, `*.log`),
- copias duplicadas locales del dataset en `flutter_app/assets/data/`,
- dependencias generadas como `node_modules/` o `vendor/`,
- cachés locales y ficheros temporales.

## Atribución de fuentes

Este proyecto usa recursos de terceros de acceso abierto. Consulta [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) para detalle de autoría, licencias y enlaces oficiales de LinguaKit y Apertium.

## Nota de licencia

Antes de distribuir salidas generadas a gran escala, revisa y cumple las licencias de los recursos externos empleados, ya que este repositorio no los contiene de forma directa.
