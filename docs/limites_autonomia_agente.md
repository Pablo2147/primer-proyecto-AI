# Límites de autonomía: agente de envíos supervisado

Agente LangChain (`create_tool_calling_agent` + `AgentExecutor`, modelo `gemini-3.5-flash-lite`) definido en `src/agente_envios_supervisado.py`. Atiende consultas de envíos y puede modificar datos y mover dinero, por eso cada herramienta tiene un nivel de supervisión distinto según su riesgo.

## Herramientas y nivel de riesgo

- `consultar_estado_envio`: **bajo** (solo lee el estado y la dirección de un envío; no modifica nada).
- `calcular_costo_envio`: **bajo** (solo calcula `500 + 120·kg + 3·km`; no ejecuta ninguna acción externa).
- `actualizar_direccion_entrega`: **medio** (escribe datos: cambia la dirección de un envío no entregado. Es reversible porque la dirección anterior queda en la observación de la traza y en `registro_cambios_direccion`. Si se usa mal, un paquete puede salir a una dirección equivocada, pero el cambio se deshace antes de la entrega).
- `generar_reembolso`: **alto** (mueve dinero de forma irreversible; un reembolso emitido no se recupera).

## Herramientas que requieren aprobación humana

- `generar_reembolso`: es la única acción del agente que no se puede deshacer y que tiene impacto económico directo. Antes de ejecutarse llama a `esperar_aprobacion`, que pide confirmación por consola con un límite de 10 segundos. Solo una respuesta `s` aprueba. Un timeout o cualquier otra respuesta cuenta como rechazo (falla segura): el reembolso no se emite y el agente recibe "Reembolso no aprobado por el supervisor humano.". Cada decisión queda en `registro_aprobaciones` y en la traza.

Las demás herramientas no piden aprobación, por razones distintas:

- `consultar_estado_envio` y `calcular_costo_envio` no cambian nada. Pedir aprobación solo agregaría fricción.
- `actualizar_direccion_entrega` se supervisa **después**, en las trazas. Un error se revierte con la dirección anterior registrada, y la propia herramienta se niega a cambiar envíos que ya figuran como entregados.

Límite conocido: la aprobación no distingue montos. Un reembolso de $100 y uno de $5000 piden lo mismo. Tampoco hay un tope de monto en el código.

## Revisión de trazas

Cada interacción se guarda como una línea JSON en `trazas_agente.jsonl` (`registrar_traza`). Cada línea tiene la entrada, cada herramienta usada con sus argumentos y su observación, y la respuesta final.

- **Frecuencia:**
  - **Todas** las trazas con `generar_reembolso`, aprobadas o no: semanalmente.
  - **Todas** las trazas con `actualizar_direccion_entrega`: semanalmente. Así un cambio erróneo se detecta antes de la entrega.
  - Las trazas solo de lectura, por muestreo: 1 de cada 20.
  - Revisión completa cada 50 interacciones si ocurre antes de la semana.
- **Qué se busca:**
  - **La misma herramienta repetida seguida en una sesión.** Se detecta con `marcar_repeticiones_sospechosas()`.
  - **Un reembolso pedido varias veces para el mismo pedido**, sobre todo después de un rechazo. `marcar_repeticiones_sospechosas` **no** lo detecta cuando cada intento es una línea distinta, así que se revisa a mano. Ejemplo real: las 4 primeras líneas del archivo (sesión `cliente_456`, de la demo manual de `agente_supervision.py`) piden el mismo reembolso de $1500 para `PED789`. Fue rechazado, rechazado, **aprobado** y rechazado. Esto es exactamente lo que hay que marcar: un reintento insistente terminó aprobando.
  - **Argumentos que no salen de la entrada del usuario:** un monto, un pedido o una dirección distintos de los que pidió el usuario.
  - **Cambios de dirección sin una petición explícita** del usuario, o hechos sobre un envío que el usuario no mencionó.
  - **Una herramienta usada para algo ajeno a su descripción**, o una respuesta final que contradice la observación de la herramienta (por ejemplo, que diga "reembolso generado" cuando la observación dice "no aprobado").

## Qué hacer ante un comportamiento inesperado

1. **Desactivar la herramienta involucrada:** quitarla de la lista `herramientas` en `src/agente_envios_supervisado.py` para que el agente no pueda volver a llamarla. Si es `generar_reembolso`, los reembolsos pasan a procesarse a mano mientras tanto.
2. **Revertir lo reversible:** si fue `actualizar_direccion_entrega`, restaurar la dirección anterior que aparece en la observación de la traza (`anterior: '...'`). Un reembolso ya emitido no se revierte desde el agente: se escala a finanzas con la línea de traza como evidencia.
3. **Aislar las trazas afectadas:** filtrar `trazas_agente.jsonl` por la herramienta o el `session_id` (`grep "generar_reembolso" trazas_agente.jsonl`) y ver si el problema se repite en otras sesiones.
4. **Identificar la causa y corregir:**
   - Si el modelo eligió mal la herramienta, ajustar el docstring.
   - Si reintentó o ignoró un rechazo, ajustar el prompt de sistema.
   - Si faltaba una validación, agregarla en el código de la herramienta (por ejemplo, la que bloquea envíos entregados).
5. **Volver a correr los casos de prueba** del `__main__` y confirmar en la traza nueva que el comportamiento cambió.
6. **Reactivar la herramienta** solo después de esa verificación, y anotar el incidente y la corrección en este documento.

## Verificación contra el código

Verificado el 2026-11-09 con `python src/agente_envios_supervisado.py`. Las respuestas al supervisor (`s` para P1, `n` para P2) se pasaron por la entrada estándar.

`grep -n "esperar_aprobacion(" src/agente_envios_supervisado.py` devuelve la definición y la única llamada, dentro de `generar_reembolso`, que es la única herramienta de riesgo alto:

```
29:def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: int = 10) -> bool:
135:    aprobado = esperar_aprobacion(mensaje)
```

`trazas_agente.jsonl` registró una interacción de cada nivel. Estas son dos líneas reales: una de riesgo medio y un reembolso rechazado.

```json
{"timestamp": "2026-11-10T01:11:23.488092+00:00", "session_id": "cliente_103", "entrada": "Cambia la dirección de entrega del envío AR12345 a Av. Siempre Viva 742", "acciones": [{"herramienta": "actualizar_direccion_entrega", "argumentos": {"nueva_direccion": "Av. Siempre Viva 742", "numero_seguimiento": "AR12345"}, "observacion": "Dirección del envío AR12345 actualizada a 'Av. Siempre Viva 742' (anterior: 'Calle Falsa 123')."}], "respuesta_final": "La dirección de entrega del envío **AR12345** ha sido actualizada exitosamente a **Av. Siempre Viva 742** (la dirección anterior era 'Calle Falsa 123')."}
{"timestamp": "2026-11-10T01:11:42.363592+00:00", "session_id": "cliente_105", "entrada": "Reembolsa el pedido P2 por $5000", "acciones": [{"herramienta": "generar_reembolso", "argumentos": {"numero_pedido": "P2", "monto": 5000}, "observacion": "Reembolso no aprobado por el supervisor humano."}], "respuesta_final": "El reembolso para el pedido P2 por $5000 no fue aprobado por el supervisor humano, por lo que no se pudo procesar."}
```

En esa corrida, cada caso usó exactamente una herramienta, la esperada. El agente no reintentó el reembolso rechazado y `marcar_repeticiones_sospechosas()` no marcó ninguna sesión.
