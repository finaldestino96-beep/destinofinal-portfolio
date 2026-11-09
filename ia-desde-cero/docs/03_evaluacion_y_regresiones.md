# 03 — Evaluación, aceptación y regresiones

## 1. Batería obligatoria
Cada versión candidata ejecuta el mismo set y un set nuevo oculto. Guardar versión de datos, semilla, prompt, salida y métrica.

| Área | Prueba | Métrica |
|---|---|---|
| Tokenizer | encode/decode | round-trip, UNK, corrupción |
| Lenguaje | continuación en textos no vistos | loss/perplejidad, muestras revisadas |
| Copia | copiar secuencias y cifras | exactitud exacta |
| Aritmética | acarreo, préstamo, ceros, multiplicación | exactitud por dificultad |
| Conversación | 5–10 turnos con referencias | continuidad, pertinencia |
| Instrucciones | resumir, explicar, comparar, clasificar | cumplimiento de rúbrica |
| Corrección | usuario corrige un dato | uso de corrección en turnos posteriores |
| Incertidumbre | preguntas sin datos suficientes | abstención apropiada, invención |
| Recuperación | preguntas sobre documentos indexados | recall@k, precisión, fidelidad |
| Robustez | errores tipográficos, paráfrasis, cambios de tema | degradación frente a control |

## 2. Rúbrica humana de conversación
Puntuar cada dimensión 0–2:
- relevancia;
- coherencia;
- seguimiento de contexto;
- cumplimiento de instrucción;
- precisión factual;
- claridad;
- reconocimiento de incertidumbre.
Definir antes de probar qué significa 0, 1 y 2. Usar al menos dos evaluadores cuando sea posible y resolver desacuerdos con ejemplos.

## 3. Criterio mínimo para “primera versión conversacional”
No declarar éxito por una sola conversación. Como puerta inicial propuesta:
- superar 90% de round-trip del tokenizer en casos normales (objetivo 100% para texto válido representable);
- mantener coherencia y referencias en al menos 8/10 diálogos multturno reservados;
- cumplir al menos 80% de tareas sencillas en rúbrica humana;
- reconocer falta de información en al menos 8/10 preguntas deliberadamente no respondibles;
- no perder más de 2 puntos porcentuales en pruebas críticas anteriores frente a baseline.
Estos umbrales son metas iniciales de ingeniería, no resultados ya alcanzados ni estándares universales. Ajustarlos tras medir baseline.

## 4. Regresión
Toda prueba fallida se convierte en caso reproducible:
- ID del caso;
- versión y hash;
- entrada y contexto;
- salida esperada y real;
- clase de fallo;
- severidad;
- corrección propuesta.
No introducir casos de test al entrenamiento sin moverlos a una partición de desarrollo; conservar un test final sellado.

## 5. Análisis de pérdida
- Train baja / validation baja: aprendizaje útil posible; revisar calidad de muestras.
- Train baja / validation se estanca o sube: sobreajuste, fuga, distribución distinta o datos insuficientes.
- Ambas altas: objetivo, datos, tokenizer, arquitectura, optimización o capacidad.
- Loss baja pero respuestas malas: objetivo no alineado con diálogo, tokenización/contexto defectuosos o evaluación que no mide utilidad.
La pérdida no demuestra comprensión por sí sola.

## 6. Control de versión
Cada experimento debe guardar checkpoint, optimizer, scheduler, RNG/seed, tokenizer, config, manifest de datos, métricas y commit de código. Promover con una referencia estable y conservar rollback.
