# Evaluacion del Colab Original

## Resumen

La idea original del cuaderno era buena, pero su implementacion tenia errores importantes.

Lo valioso del enfoque original:

- Separaba el problema en fases razonables: deteccion de conflictos, limpieza, alineacion simple y alineacion con compuestos.
- Aprovechaba la salida estructurada de LinguaKit en JSON para alinear por `code_tense` y `person`.
- Introducia decisiones linguisticas utiles para este proyecto, como:
  - alinear tiempos simples ES-GL por codigos de tiempo,
  - tratar el infinitivo conjugado gallego como caso especial,
  - aproximar ciertos compuestos del castellano con estructuras gallegas equivalentes,
  - registrar incidencias en logs en vez de fallar silenciosamente.
- En la practica, al adaptarlo, vimos que la parte de alineacion simple reproduce bien el lote real y que la salida completa cruda tambien estaba bastante cerca de lo que el cuaderno queria hacer.

## Por Que La Idea Era Buena

El cuaderno intentaba resolver el problema correcto:

1. Cargar pares ES-GL.
2. Conjugar ambos lados.
3. Detectar verbos conflictivos o no conjugables.
4. Excluir esos casos del alineamiento.
5. Generar tablas alineadas de formas verbales con metadatos de tiempo y persona.

Ese diseño encaja con el objetivo real del repositorio y con la estructura de datos que consumen las interfaces.

## Donde Fallaba La Implementacion

### 1. No era un script Python ejecutable

El archivo exportado desde Colab contenia sintaxis de notebook como:

- `!rm`
- `!sort`
- `!cpan`

Eso funciona en Colab o Jupyter, pero no en un `.py` normal.

### 2. Tenia errores de sintaxis reales

Habia bloques que ni siquiera compilaban por paréntesis y listas mal cerradas en llamadas a `subprocess.call`.

Eso impide ejecutar el archivo sin antes repararlo manualmente.

### 3. Mezclaba prototipo interactivo con automatizacion

El cuaderno estaba escrito como flujo exploratorio:

- imprime datasets por pantalla,
- hace revisiones manuales intermedias,
- presupone contexto de notebook,
- inserta palabras “a mano” en listas internas,
- depende de comandos shell embebidos.

Eso lo hace util para investigacion, pero fragil para automatizacion reproducible.

### 4. Serializaba mal los datos

Guardaba diccionarios Python con `echo` a ficheros y luego intentaba reconstruirlos reemplazando comillas.

Eso es arriesgado porque:

- no es JSON real,
- puede romper cadenas complejas,
- depende del formato textual de Python,
- vuelve fragil la lectura posterior.

### 5. La deduplicacion final era incorrecta

Usaba una estrategia equivalente a `uniq -u` para los archivos `*_pro`.

Eso no conserva una copia de cada fila repetida, sino que elimina por completo cualquier fila que aparezca mas de una vez.

Como consecuencia, una alineacion valida repetida puede desaparecer del resultado.

### 6. El alineamiento dependia demasiado del orden de los ficheros

En varios pasos emparejaba las lineas ES y GL con `zip(...)`.

Eso solo es seguro si ambos ficheros:

- tienen exactamente el mismo numero de lineas,
- estan en el mismo orden,
- nunca pierden una entrada por el camino.

Si una linea falta o se desplaza, el cuaderno empieza a alinear verbos incorrectos entre si.

### 7. La logica de compuestos era dificil de verificar

La parte de tiempos compuestos tenia:

- indentacion delicada,
- pasos especiales no evidentes,
- reutilizacion de estructuras de tiempos simples,
- casos particulares como `FN-IP` y `FN(Inf)-IP` mezclados en distintas pasadas.

Al adaptarla, se vio que hacia falta depurarla con datos reales para reproducir exactamente el comportamiento del lote.

## Comparacion Con Nuestra Implementacion Inicial

Frente a [corpus_verbal.py](C:/Users/rodri/OneDrive/Documentos/GitHub/relacion_formas_verbais_galego_castelan/corpus_verbal.py), el cuaderno original estaba peor implementado como software:

- nuestra implementacion inicial era un script Python real,
- tenia estructura de CLI,
- era mas mantenible,
- era mas segura en entrada y salida,
- no dependia de sintaxis de notebook,
- y estaba mejor preparada para ejecutarse en el repo.

En cambio, el cuaderno original aportaba sobre todo valor como referencia conceptual y linguistica.

## Conclusion

La idea original era buena porque atacaba correctamente el problema de alineacion verbal ES-GL y proponia varias decisiones utiles para el dominio.

La implementacion, sin embargo, tenia errores serios:

- no era ejecutable como `.py`,
- mezclaba logica valida con restos de Colab,
- usaba serializacion fragil,
- dependia de orden implicito en los ficheros,
- y deduplicaba mal los resultados finales.

La forma correcta de aprovechar ese trabajo no era usarlo tal cual, sino adaptarlo y validarlo contra datos reales, que es justo lo que se hizo despues.
