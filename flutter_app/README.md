# Flutter App

Cliente Flutter para explorar el mismo corpus verbal ES-GL que usa la interfaz Angular.

## Qué incluye

- Búsqueda por infinitivos y por cualquier forma conjugada.
- Filtros por tiempo y persona.
- Ordenación de pares y de la tabla de alineaciones.
- Diseño responsive pensado para escritorio y tablet.

## Preparación

1. Instala Flutter en tu máquina.
2. Desde `flutter_app/`, genera el esqueleto de plataformas si aún no existe:

```powershell
flutter create .
```

3. Copia los datos desde la app Angular:

```powershell
powershell -ExecutionPolicy Bypass -File .\tool\sync_assets.ps1
```

## Ejecución

```powershell
flutter pub get
flutter run
```

## Datos

La app espera estos ficheros dentro de `assets/data/`:

- `verbos_relacionados.tsv`
- `alineaciones_completas.tsv`

No se versionan en esta carpeta para evitar duplicar un dataset grande; el script `tool/sync_assets.ps1` los sincroniza desde `web-angular/src/assets/data/`.
