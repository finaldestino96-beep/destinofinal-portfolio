# 04 — Investigación técnica y fuentes

Fecha de consulta: 2026-11-09. Fuentes primarias/documentación oficial cuando están disponibles. Los resultados de investigación son orientación, no una receta universal.

## Métodos actuales que sí se pueden aplicar
1. **Preentrenamiento autoregresivo:** entrenar a predecir el siguiente token; requiere tokenizer consistente, secuencias y máscara causal correcta.
2. **Supervised Fine-Tuning (SFT):** ejemplos de instrucciones y conversaciones con respuestas esperadas. La documentación TRL admite formatos de texto, prompt-completion y mensajes conversacionales; permite calcular pérdida solo en respuestas del asistente cuando la plantilla soporta máscaras.
3. **Optimización de preferencias (DPO):** usar pares de respuestas preferida/no preferida después de que el modelo ya genere respuestas razonables. No sustituye preentrenamiento ni datos buenos.
4. **Recuperación aumentada (RAG):** consultar documentos externos para conocimiento amplio/actualizable; separa memoria documental de pesos.
5. **Evaluación continua:** conjuntos de validación/test, métricas por categoría, muestras manuales, regresión y versionado.
6. **Escalado medido:** aumentar parámetros, tokens o contexto solo después de estimar el cuello de botella y medir el presupuesto.

## Realidad de escala
El trabajo de Hoffmann et al. (Chinchilla, 2022) estudió modelos de 70M a más de 16B parámetros y encontró que, bajo su régimen de cómputo, tamaño y tokens de entrenamiento deben escalar juntos; la conocida aproximación de ~20 tokens por parámetro es una referencia de aquel régimen, no una ley universal ni una garantía para un modelo diminuto. No usarla para prometer calidad.
Si el proyecto realmente tiene ~2.09M parámetros, multiplicar por 20 daría ~41.8M tokens como simple referencia aritmética; eso **no** significa que esa cantidad convierta el modelo en un asistente competente. La capacidad del modelo sigue siendo el límite central y las leyes se extrapolan con cautela.

## Lo que hoy puede lograrse con recursos modestos
- Prototipos pequeños para aprender tokenización, entrenamiento, generación y diálogo acotado.
- Modelos especializados en tareas estrechas, especialmente con herramientas deterministas o recuperación.
- Fine-tuning de modelos abiertos preentrenados para lograr utilidad conversacional mucho antes que preentrenar un modelo competitivo desde cero.
- No es realista prometer un equivalente de ChatGPT desde ~2M parámetros y un corpus pequeño. Un sistema competitivo exige escala de datos, parámetros, cómputo, evaluación, seguridad y trabajo continuo.

## Referencias
- Hugging Face TRL — SFT Trainer, formatos de diálogo y entrenamiento supervisado: https://huggingface.co/docs/trl/en/sft_trainer
- Hugging Face TRL — métodos de post-entrenamiento (SFT, DPO, GRPO, reward modeling): https://huggingface.co/docs/trl/en/index
- Hoffmann et al., *Training Compute-Optimal Large Language Models* (2022): https://arxiv.org/abs/2203.15556
- NeurIPS 2022, análisis empírico de entrenamiento compute-optimal: https://proceedings.neurips.cc/paper_files/paper/2022/hash/c1e2faff6f588870935f114ebe04a3e5-Abstract.html
- Sardana et al., *Beyond Chinchilla-Optimal* (ICML 2024), incluye coste de inferencia: https://proceedings.mlr.press/v235/sardana24a.html
- Kaplan et al., *Scaling Laws for Neural Language Models* (2020): https://arxiv.org/abs/2001.08361
- Lovelace et al., *Prescriptive Scaling Laws for Data Constrained Training* (2026): https://arxiv.org/abs/2605.01640

## Decisión recomendada
Mantener la vía desde cero como investigación propia, pero medirla honestamente. Si la prioridad inmediata cambia a “asistente útil ya”, crear un carril separado con un modelo abierto preentrenado y SFT/LoRA; no mezclar pesos ni presentar ese resultado como IA entrenada desde cero.
