# Web PHP

Cliente en PHP puro para navegar el corpus ES-GL sin framework frontend.

## Funcionalidades

- Búsqueda por infinitivo y por formas conjugadas asociadas.
- Filtros por tiempo y persona.
- Ordenación de pares y de la tabla.
- Renderizado server-side con cache de parseo del corpus.

## Ejecución local

```powershell
cd .\web-php
php -S localhost:8082 -t public
```

Abre `http://localhost:8082`.

## Docker

Desde la raíz del repositorio:

```powershell
docker compose up --build web-php
```

La versión dockerizada queda disponible en `http://localhost:28182`.

## Datos

La aplicación lee los TSV desde `../web-angular/src/assets/data/` en desarrollo local.
En Docker, esos mismos ficheros se copian a la imagen durante el build.
