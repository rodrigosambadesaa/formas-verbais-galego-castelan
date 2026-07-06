# Web Angular

Cliente Angular 17 para navegar el corpus ES-GL de formas verbales alineadas.

## Funcionalidades

- Búsqueda de pares por infinitivo o por cualquier forma conjugada asociada.
- Filtro adicional sobre la tabla por forma, tiempo, persona o infinitivo.
- Ordenación de la lista de pares por verbo ES, verbo GL o número de formas.
- Ordenación interactiva de la tabla por cualquier columna.
- Vista responsive para escritorio y móvil.

## Desarrollo

```powershell
npm install
npm start
```

La aplicación queda disponible en `http://localhost:4200`.

## Build

```powershell
npm run build
```

## Datos

La app lee:

- `src/assets/data/verbos_relacionados.tsv`
- `src/assets/data/alineaciones_completas.tsv`

Si falta `alineaciones_completas.tsv`, la interfaz sigue arrancando, pero la búsqueda completa de formas quedará deshabilitada.
