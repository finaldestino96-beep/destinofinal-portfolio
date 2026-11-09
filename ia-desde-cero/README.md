# IA propia desde cero — expediente v15

> Estado: planificación técnica y auditoría pendiente. Fecha de corte: 2026-11-09.

Este directorio reúne la hoja de ruta para convertir el proyecto neuronal propio (sin modelo base preentrenado) en un sistema conversacional evaluable. Está separado del sitio de portafolio y vive en la rama `ia-v15-ruta-conversacional`.

## Qué contiene
- [Estado y brecha](docs/00_estado_y_brecha.md): qué consta, qué falta y qué debe verificarse.
- [Ruta de entrenamiento](docs/01_ruta_entrenamiento.md): secuencia técnica recomendada.
- [Datos y tokenización](docs/02_datos_tokenizacion.md): preparación de corpus y formato de diálogo.
- [Evaluación y control de regresiones](docs/03_evaluacion_y_regresiones.md): pruebas de aceptación.
- [Investigación y decisiones actuales](docs/04_investigacion_y_referencias.md): métodos vigentes y fuentes.
- [Especificación operativa](docs/05_especificacion_operativa.md): flujo ejecutable, artefactos, criterios de promoción.
- [Registro de experimentos](templates/registro_experimento.md).
- [Ejemplo de diálogo JSONL](templates/dialogo_ejemplo.jsonl).
- [Configuración inicial ilustrativa](configs/experimento_inicial.yaml).

## Diagnóstico ejecutivo
Las notas históricas describen una red desde cero y una v15 con mejoras en copia numérica y operaciones por columnas. Se reportaron 16/16 en una batería de copia y un tamaño histórico aproximado de 2,090,880 parámetros. **Nada de eso se ha verificado contra el repositorio, checkpoint o logs actuales.** No se ha demostrado todavía comprensión semántica general ni conversación sostenida.

Si el tamaño real fuera cercano a 2.09 M de parámetros, debe tratarse como un modelo experimental pequeño: puede servir para aprender y demostrar tareas acotadas, pero no es realista esperar calidad conversacional general comparable con ChatGPT solo añadiendo libros. La arquitectura, datos, cómputo y evaluación determinan el resultado.

## Regla de seguridad
No se subieron pesos, datasets privados, credenciales ni código fuente de la v15 porque no están disponibles en esta sesión. No reemplazar ni borrar el checkpoint original. Trabajar siempre con copias y publicar artefactos solo después de revisar licencias y privacidad.

## Próximo paso obligatorio
Colocar el proyecto real v15 en el repositorio o facilitar sus archivos: arquitectura, entrenamiento, tokenizer/vocabulario, checkpoint `modelo.pt`, configuración, logs, pruebas y dataset/manifiestos. Entonces completar la auditoría y reemplazar las estimaciones por mediciones.

## Estado de este branch
- [x] Crear rama aislada para documentación.
- [x] Documentar estado conocido y brechas.
- [x] Diseñar ruta de entrenamiento y evaluación.
- [ ] Auditar el código y checkpoint reales.
- [ ] Medir tokens, parámetros, throughput, memoria y tiempo.
- [ ] Ejecutar baseline reproducible y primera fase conversacional.
