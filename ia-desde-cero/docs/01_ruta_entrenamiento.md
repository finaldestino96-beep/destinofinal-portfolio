# 01 — Ruta de entrenamiento priorizada

## Principio
La ruta rápida es eliminar incertidumbre técnica antes de gastar cómputo. Congelar v15, verificar la tubería y medir baseline; después entrenar lenguaje y diálogo en una rama experimental. No introducir grandes libros sin tokenizador, particiones y objetivo.

## Fase 0 — Congelar y auditar
1. Copiar el checkpoint v15 a un directorio de solo lectura y calcular SHA-256.
2. Guardar commit del código, versión de Python/PyTorch, sistema, GPU/CPU y dependencias.
3. Contar parámetros entrenables y no entrenables desde el modelo cargado.
4. Exportar arquitectura, dimensiones, número de capas/cabezas, embedding, posición, contexto máximo y tamaño de vocabulario.
5. Guardar tokenizer y probar ida/vuelta texto→IDs→texto, incluyendo tildes, ñ, emojis, saltos, signos, números y palabras fuera de vocabulario.
6. Ejecutar todas las pruebas históricas y guardar entradas, salidas, métricas y semilla.
7. No modificar el checkpoint de referencia.

**Salida requerida:** `audit.json`, `baseline_results.json`, `environment.txt`, hash del checkpoint y una copia intacta.

## Fase 1 — Validar un modelo de lenguaje mínimo
Antes de corpus grande, usar un conjunto pequeño de texto español con licencia clara:
- verificar que el objetivo de entrenamiento esté bien implementado;
- comprobar desplazamiento input/target (el target debe ser el siguiente token);
- comprobar máscara causal si la arquitectura es autoregresiva;
- confirmar que padding no se entrena como contenido;
- sobreajustar deliberadamente un microconjunto para comprobar que la pérdida puede bajar y que el modelo memoriza ese microconjunto;
- después evaluar en textos separados no vistos.

Si ni siquiera puede sobreajustar un microconjunto, depurar código/gradientes antes de escalar.

## Fase 2 — Preentrenamiento lingüístico experimental
1. Fijar tokenizer/vocabulario antes de entrenar; cambiarlo después rompe la correspondencia de embeddings salvo migración explícita.
2. Crear corpus con deduplicación exacta y aproximada, filtrado de basura, idioma y calidad.
3. Separar train/validation/test por documento o fuente, no por líneas aleatorias de un mismo documento.
4. Empaquetar secuencias hasta la longitud de contexto real soportada.
5. Entrenar predicción del siguiente token con AdamW como baseline, warmup y scheduler documentados; los valores concretos se eligen con pruebas de estabilidad y presupuesto, no se inventan.
6. Medir loss de train y validation, tokens procesados/segundo, uso de RAM/VRAM, grad norm, tasa de NaN y muestras generadas.
7. Guardar checkpoints frecuentes y estados de optimizador/scheduler para reanudar exactamente.
8. Detener o ajustar si validation deja de mejorar, se abre brecha train/validation o aparecen colapsos/repetición.

## Fase 3 — Ajuste supervisado conversacional (SFT)
Usar datos con estructura de mensajes:
```json
{"messages":[{"role":"user","content":"¿Qué es una red neuronal?"},{"role":"assistant","content":"Es un modelo computacional que aprende patrones ajustando parámetros a partir de ejemplos."}]}
```
- Incluir conversaciones de múltiples turnos y variedad de intenciones.
- Entrenar preferentemente la pérdida sobre tokens de respuesta del asistente; verificar las máscaras.
- Incluir ejemplos donde el asistente pide información faltante y reconoce que no sabe.
- No entrenar respuestas falsas como hechos.
- Balancear temas y longitudes para que no aprenda solo un patrón de respuesta.
- Mantener un conjunto de evaluación no visto.

## Fase 4 — Preferencias y calidad de respuesta (solo cuando SFT funcione)
Recolectar pares de respuestas para la misma instrucción: respuesta preferida y no preferida, evaluadas por criterios claros. Se puede experimentar con DPO u otro método de optimización de preferencias, pero no antes de tener un modelo que ya produzca respuestas útiles. Preferencias humanas ruidosas pueden enseñar sesgos o estilo sin mejorar factualidad.

## Fase 5 — Memoria y recuperación
No intentar almacenar todos los libros en pesos. Crear índice documental externo con fragmentos, metadatos y fuente; recuperar pasajes relevantes al responder. Mantener separado:
- contexto temporal de la conversación;
- memoria persistente aprobada;
- corpus/documentos consultables.
Evaluar recuperación por precisión y cobertura, y respuestas por fidelidad a las fuentes.

## Fase 6 — Herramientas
Integrar calculadora, búsqueda o código como herramientas aisladas. El modelo debe decidir cuándo invocarlas; cada resultado debe validarse. La exactitud del wrapper no se debe reportar como habilidad neuronal.

## Fase 7 — Promoción y reversión
Una versión candidata solo reemplaza a la estable si:
- mejora la métrica objetivo;
- no cae por debajo de umbrales en pruebas previas;
- no empeora seguridad, copia ni cálculo;
- es reproducible desde datos/configuración registrados.
Si falla, conservar logs, rechazar y volver al checkpoint estable.

## Fase 8 — Matemáticas completas y razonamiento verificable
Seguir el currículo y los criterios de docs/06_matematicas_y_diagramas.md. No saltar directamente a derivadas si la IA todavía falla en álgebra y funciones. Separar conocimiento conceptual, resolución paso a paso, cálculo numérico y cálculo simbólico. Las respuestas numéricas críticas deben poder verificarse con pruebas independientes.

## Ciclo de cierre obligatorio después de CADA fase
1. Congelar el checkpoint candidato y calcular hash; conservar el checkpoint estable anterior.
2. Registrar datos, licencia/origen, tokenizer, configuración, semilla, hardware, tokens procesados y duración.
3. Medir train y validation; guardar curvas y muestras generadas.
4. Ejecutar la batería completa de regresión: copia, aritmética, conversación multturno, instrucciones, temáticas y matemáticas ya aprobadas.
5. Ejecutar pruebas nuevas no vistas para la capacidad de la fase.
6. Revisar errores por categoría y determinar si hay sobreajuste, memorización, pérdida de contexto o regresión.
7. Emitir informe: aprobado / repetir / corregir / revertir, con evidencia y umbrales.
8. Promover el checkpoint solo si cumple los umbrales predefinidos; si no, volver al estable sin borrar el candidato ni sus logs.
9. Actualizar la matriz de capacidades y la brecha restante.

No pasar automáticamente a la siguiente fase por haber terminado una cantidad de épocas. El criterio es rendimiento medido y ausencia de regresiones.
