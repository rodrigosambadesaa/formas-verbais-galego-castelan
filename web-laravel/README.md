# Web Laravel

Cliente Laravel para explorar el corpus verbal ES-GL con la misma funcionalidad base que Angular, Flutter y PHP puro.

## Funcionalidades

- Búsqueda por infinitivo o forma conjugada.
- Filtros por tiempo y persona.
- Ordenación de pares y resultados.
- Cache del corpus usando la infraestructura de Laravel.

## Ejecución local

Si ya tienes dependencias instaladas:

```powershell
cd .\web-laravel
php artisan serve --host=127.0.0.1 --port=8083
```

Abre `http://127.0.0.1:8083`.

## Docker

Desde la raíz del repositorio:

```powershell
docker compose up --build web-laravel
```

La versión dockerizada queda disponible en `http://localhost:28183`.

## Datos

En desarrollo local, Laravel lee el corpus desde `../web-angular/src/assets/data/`.
En Docker, los TSV se copian dentro de la imagen y se exponen mediante `CORPUS_DATA_DIR=/var/www/data`.
