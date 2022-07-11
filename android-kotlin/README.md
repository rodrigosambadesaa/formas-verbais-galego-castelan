# Android nativo en Kotlin · Formas verbais ES-GL

Cliente Android nativo, sen servizo remoto nin permisos de rede. Funciona sen
conexión a Internet despois de instalalo e permite:

- Buscar por infinitivos e formas conxugadas en galego e castelán.
- Filtrar as formas por tempo e persoa.
- Ver o infinitivo ao que pertence cada forma e consultar pares ES-GL.
- Buscar sen distinguir maiúsculas nin acentos, cun máximo de 250 filas por
  consulta para non saturar a pantalla.

## Datos

`app:prepareCorpusAssets` copia durante a compilación dous recursos
versionados **nun único lugar** no repositorio:

- `../web-angular/src/assets/data/verbos_relacionados.tsv`
- `../formas_verbais_es_gl_completo.txt` (como `alineaciones_completas.tsv`)

O formato das aliñacións é `forma_es<TAB>forma_gl<TAB>tempo<TAB>persoa`.
Cada grupo comeza con `FN-FN<TAB>Inf`, que identifica os dous infinitivos.
A aplicación non inventa conxugacións: só consulta as liñas documentadas no corpus.
As entradas sen marcador de grupo anterior non se atribúen a ningún verbo.

## Construír e probar

Requírese Android SDK 35, Java 17 e Gradle 8.11.1:

```sh
cd android-kotlin
gradle testDebugUnitTest assembleDebug
```

APK: `app/build/outputs/apk/debug/app-debug.apk`.

O workflow `.github/workflows/android-kotlin.yml` executa validación
do corpus, probas unitarias e compilación, e publica o APK como artefacto
de GitHub Actions. O código fonte non duplica o corpus de ~12 MB.

## Alcance

É unha app Android nativa en Kotlin (non Flutter). Non modifica os outros
catro clientes nin require instalar LinguaKit no teléfono.
