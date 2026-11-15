# Reconstrucción cronológica documentada

El cliente Kotlin se desarrolló en **noviembre de 2026**. El usuario solicitó
insertarlo en la secuencia histórica fechada en 2022. Por esa razón, se
preparó una **reconstrucción del historial**, no una afirmación de que este
código existiese realmente en 2022.

El commit reconstruido se ubica **después** de `9d4b1db2` («Add Flutter
interface», 10 de julio de 2022) y **antes** de `73cd01b0`
(«Updates», 11 de julio de 2022). Su fecha reconstruida es
`2022-07-11 10:37:00 +02:00` (hora peninsular española).

Se preservó una referencia al historial anterior en
`backup/master-before-android-history-rewrite`; la rama
`historical/android-kotlin-2022` permite auditar la reconstrucción. Esta
operación genera nuevos SHA para todos los commits descendientes, aunque
preserva sus cambios. El parche de seguridad de octubre de 2026 se
mantiene en el nuevo historial.

**Importante:** la fecha Git reconstruida no prueba la fecha real de
autoría, pruebas o publicación del código.
