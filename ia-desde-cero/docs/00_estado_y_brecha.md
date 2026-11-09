# 00 — Estado real conocido y análisis de brecha

Fecha de corte: 2026-11-09. Fuente del estado: notas de conversaciones anteriores, no inspección de código.

## 1. Inventario de lo que se ha informado
| Componente/capacidad | Evidencia histórica disponible | Estado verificable ahora |
|---|---|---|
| Red neuronal propia desde cero | El usuario ha indicado que no usa un modelo base | No inspeccionada |
| Parámetros | Aproximadamente 2,090,880 en notas de una versión | Pendiente contar en checkpoint |
| Checkpoint | Archivo llamado `modelo.pt` | No recibido en esta sesión |
| Copia numérica | v14/v15 reportaron 16/16 en una batería | Prueba, datos y log pendientes |
| Aritmética | Correcciones por columnas, acarreo/préstamo y multiplicación por etapas | Repetir pruebas |
| Tokenizador/vocabulario | Se sabe que hay lector/tokenización en el proyecto, sin detalle técnico suficiente | Pendiente |
| Lenguaje natural | Sin benchmark conocido | No demostrado |
| Conversación multturno | Sin batería ni resultados aportados | No demostrado |
| Comprensión/razonamiento general | No hay evaluación controlada aportada | No demostrado |
| Aprendizaje estable sin regresión | Se han hecho versiones sucesivas, pero falta protocolo reproducible | Parcial/pendiente |

## 2. Brecha hacia una IA conversacional
**Brecha A — Integridad de la tubería:** verificar normalización de texto, tokenizer, IDs, máscara de atención, etiquetas, padding, truncamiento y reconstrucción de salida. Si falla aquí, todo entrenamiento lingüístico posterior queda contaminado.

**Brecha B — Modelo de lenguaje:** confirmar que la arquitectura puede procesar secuencias y aprender predicción del siguiente token (o justificar otro objetivo). Una red entrenada solo para copia/cálculo no se convierte automáticamente en un modelo de lenguaje.

**Brecha C — Diálogo:** enseñar formato de roles, turnos, contexto previo, referencias y cierre de turno. Un corpus de libros no sustituye ejemplos de diálogo.

**Brecha D — Instrucciones:** ejemplos variados de explicación, resumen, comparación, extracción, clasificación y aclaración cuando falte información.

**Brecha E — Fiabilidad:** conjuntos reservados de evaluación, calibración de incertidumbre, detección de respuestas inventadas, análisis de errores y pruebas de regresión.

**Brecha F — Escala:** capacidad, diversidad/calidad de datos y cómputo suficientes. Si la cifra de ~2.09 M parámetros es correcta, el límite de capacidad es severo para conversación general; no se resuelve solo aumentando épocas o repitiendo los mismos textos.

## 3. Dos objetivos distintos; no confundirlos
1. **IA desde cero (objetivo de propiedad/aprendizaje):** mantener arquitectura y pesos propios; entrenar lenguaje y diálogo desde inicialización aleatoria. Es un proyecto de investigación, con resultados modestos al principio y necesidad de recursos crecientes.
2. **Asistente útil a corto plazo (objetivo de producto):** partir de un modelo abierto preentrenado y adaptarlo mediante SFT/LoRA, recuperación documental y herramientas. Es mucho más rápido, pero ya no sería un modelo base entrenado desde cero.

El proyecto puede mantener ambos carriles en paralelo, pero no llamar al segundo “entrenamiento desde cero”.

## 4. Qué significa “conversacional” en términos comprobables
Versión mínima conversacional cuando supera un set oculto y no visto durante entrenamiento:
- respuesta pertinente a preguntas sencillas nuevas;
- coherencia y continuidad durante 5–10 turnos;
- uso correcto de referencias recientes (“eso”, “la segunda opción”);
- ejecución de instrucciones de una tarea;
- capacidad de pedir aclaración;
- reconocimiento de incertidumbre;
- sin regresión grave en copia y cálculo.

Esto no equivale a comprensión humana ni a inteligencia general. Son criterios operativos y medibles.

## 5. Decisiones pendientes de auditoría
No fijar todavía learning rate, batch size, épocas, contexto, tamaño de vocabulario, cantidad de tokens o fecha de entrega. Esos valores dependen de arquitectura, hardware, precisión numérica, longitud de secuencia, throughput y curva de validación. Medir primero.

## 6. Avances que ya se consideran realizados (historial)
No reiniciar desde cero las tareas ya completadas. Las conversaciones anteriores informan: construcción de la red neuronal propia, entrenamiento iterativo hasta v15, mejoras de copia numérica hasta 16/16 en la batería reportada, y correcciones de suma/resta por columnas con acarreo/préstamo y multiplicación por etapas. Se conservan como baseline histórico. Para afirmar que siguen funcionando tras nuevas fases, se ejecuta la misma batería y se comparan resultados; la repetición es verificación de no-regresión, no rehacer el trabajo.

## 7. Nueva brecha: matemáticas generales y representación visual
El historial respalda trabajo en aritmética elemental, pero no demuestra todavía álgebra general, geometría, trigonometría, cálculo diferencial/integral, probabilidad, estadística, álgebra lineal, matemática discreta ni demostraciones. Tampoco hay benchmark confirmado de diagramas. Estas capacidades se desarrollarán en progresión y se evaluarán por separado.
