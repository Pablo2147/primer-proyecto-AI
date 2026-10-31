# Límites de la métrica de evaluación

## Qué mide

Coincidencia de palabras entre una respuesta generada y una referencia, contando repeticiones (precisión, cobertura, F1).

## Modos de falla conocidos

- Las respuestas correctas pero largas puntúan bajo, porque la precisión cae con cada palabra extra. Ejemplo: "¿Qué es Python?" responde bien, pero con características y usos que exceden la referencia: precisión 0.02, cobertura 1.0, F1 0.04.
- Las respuestas que mencionan alternativas junto a la correcta se penalizan igual que las erróneas. Ejemplo: "¿Cuántos continentes hay?" responde 6 (correcto), pero añade respuesta 4, 5 y 7 continentes: F1 0.03, el más bajo de la muestra.
- Una respuesta directa y correcta no llega a 1.0 si reformula la pregunta con otras palabras que la referencia. Ejemplo: "¿Cuántos jugadores tiene un equipo de fútbol en cancha?" responde "11 jugadores" y aclara "10 de campo y 1 portero": F1 0.55; "¿Cuál es la capital de Chile?" responde Santiago correctamente y obtiene F1 0.67.
- Por construcción, la métrica no distingue datos incorrectos ni negaciones ausentes (por ejemplo, una fecha equivocada o un "no" omitido dentro de una oración que por lo demás coincide). **No se observó ningún caso así en la muestra revisada**: es un límite esperado por cómo se calcula, no uno verificado.

## Muestra revisada

10 casos revisados a mano: los 5 con menor F1 (0.03 a 0.10) y los 5 con mayor F1 (0.55 a 1.00), sobre las 20 respuestas de `resultados_metricas.json` generadas el 2026-10-30. Se evaluó corrección factual, completitud y contradicción (ver `src/revision_manual.py`). Los 10 resultaron factualmente correctos, completos y sin contradicciones. Al ser una muestra de extremos, no cubre los casos intermedios.

## Recomendación de uso

Usar F1 para comparar en volumen entre versiones del cliente, siempre sobre las mismas consultas. No interpretar un F1 bajo como respuesta incorrecta: en esta muestra los puntajes más bajos fueron respuestas correctas y extensas. Revisar siempre a mano cualquier respuesta con fechas, cifras o nombres propios, y las respuestas largas o con matices.
