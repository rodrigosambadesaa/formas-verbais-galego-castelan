# Reconstrucción cronológica documentada

El cliente Kotlin se desarrolló en **noviembre de 2026**. El usuario solicitó
insertarlo en la secuencia histórica fechada en 2022. Por esa razón, se
preparó una **reconstrucción del historial**, no una afirmación de que este
código existiese realmente en 2022.

El commit de incorporación a la historia se ubica a continuación del commit
`6972b638` («Add Flutter interface», 10 de julio de 2022), con fecha
`2022-07-10 11:23:00 +02:00` (hora peninsular española).

Se preservó una referencia al historial anterior en
`backup/master-before-android-history-rewrite`; la rama
`historical/android-kotlin-2022` permite auditar la reconstrucción. Esta
operación genera nuevos SHA para todos los commits descendientes, aunque
preserva sus cambios. El parche de seguridad de octubre de 2026 se
mantiene en el nuevo historial.

**Importante:** la fecha Git reconstruida no prueba la fecha real de
autoría, pruebas o publicación del código.
