# 05 — Especificación operativa para el ejecutor

Este documento define el trabajo que debe realizarse cuando se incorporen los archivos reales. No asumir rutas ni nombres de scripts que aún no se han inspeccionado.

## Entrada requerida
- Código fuente completo de v15.
- Checkpoint(s) y hash.
- Tokenizer/vocabulario y configuración.
- Dataset o manifiesto de fuentes/licencias.
- Logs, pruebas, resultados previos.
- Información de hardware y entorno.

## Orden obligatorio del trabajo
### A. Inventario sin modificar
1. Listar archivos y tamaños.
2. Identificar punto de entrada, arquitectura, trainer, dataset loader, tokenizer y evaluador.
3. Identificar cualquier módulo externo que calcule o corrija resultados.
4. Buscar secretos y excluirlos de Git.
5. Crear informe de inventario y mapa de dependencias.

### B. Reproducibilidad
1. Crear entorno reproducible con versiones fijadas.
2. Ejecutar tests existentes.
3. Cargar checkpoint en modo seguro.
4. Contar parámetros y guardar arquitectura/configuración.
5. Repetir baseline con semilla registrada.
6. Comparar contra métricas históricas; marcar discrepancias.

### C. Diagnóstico del modelo lingüístico
1. Confirmar que el modelo recibe secuencias de tokens.
2. Confirmar que predice el siguiente token o documentar el objetivo alternativo.
3. Verificar desplazamiento de labels, máscara causal, padding, EOS y truncamiento.
4. Probar overfit de microdataset.
5. Generar muestras y evaluar en texto no visto.
6. Decidir: corregir tubería, continuar v15 o entrenar un modelo lingüístico separado.

### D. Entrenamiento conversacional experimental
1. Crear dataset JSONL con roles validados.
2. Deduplicar y separar por conversaciones/documentos.
3. Añadir validación de esquema y longitud.
4. Entrenar una copia, nunca el checkpoint de referencia.
5. Guardar checkpoints y estados completos.
6. Evaluar en conjunto oculto y ejecutar regresiones.
7. Documentar ejemplos de aciertos y fallos.

### E. Informe de brecha final
Entregar tabla con:
- capacidad;
- evidencia;
- prueba;
- resultado medido;
- brecha;
- prioridad;
- estimación de coste/tiempo basada en throughput medido;
- decisión: aprobado, parcial, no demostrado o bloqueado.

## Reglas de no-regresión
- No sobrescribir `modelo.pt` original.
- No borrar datos ni logs.
- No modificar tokenizer sin versión nueva.
- No entrenar con el conjunto test sellado.
- No publicar pesos o corpus sin verificar licencias y privacidad.
- No declarar comprensión general a partir de loss o demos seleccionadas.

## Artefactos que debe producir cada experimento
`audit.json`, `data_manifest.json`, `tokenizer_report.json`, `train_config.yaml`, `metrics.jsonl`, `samples.jsonl`, `regression_report.md`, checkpoint y SHA-256.

## Criterio de salida
La fase termina solo cuando otra persona puede repetir el experimento con los mismos archivos/configuración y obtener resultados comparables, con diferencias explicadas.
