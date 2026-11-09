# 02 — Datos, tokenización y formato

## 1. Tipos de datos: no son intercambiables
- **Texto general:** enseña regularidades del idioma, vocabulario y estilo.
- **Diálogo:** enseña turnos, respuestas, seguimiento del tema y referencias.
- **Instrucciones:** enseña a realizar tareas bajo una petición.
- **Preferencias:** enseña cuál de dos respuestas se considera mejor según criterios.
- **Conocimiento verificable:** preguntas/respuestas respaldadas por fuentes; mejor con recuperación documental cuando el dato cambia.
- **Evaluación:** ejemplos reservados que nunca entran al entrenamiento.

Los libros ayudan al lenguaje y al estilo narrativo, pero no bastan para enseñar conversación útil.

## 2. Calidad y gobernanza
Para cada fuente guardar: URL/autor/editor, fecha de obtención, licencia/permiso, idioma, checksum, política de uso y versión. Excluir secretos, datos personales no autorizados, spam, texto corrupto y duplicados. Respetar derechos de autor y condiciones de las fuentes. No subir datasets con datos personales o licencias dudosas a un repositorio público.

## 3. Limpieza y particiones
- UTF-8 y normalización Unicode consistente (documentar NFC/NFKC).
- Eliminar boilerplate, navegación, HTML residual y duplicados.
- Detectar idioma y filtrar muestras fuera del español objetivo.
- Deduplicar exacta y aproximadamente.
- Dividir por documento/fuente en train, validation y test para evitar fuga.
- Mantener test sellado y versionado; no usarlo para elegir hiperparámetros.

## 4. Tokenizador
Auditar:
- estrategia (caracteres, BPE, unigram u otra);
- vocabulario y tamaño;
- tokens especiales: BOS, EOS, PAD, UNK y marcadores de rol;
- tratamiento de espacios, acentos, ñ, signos, números y texto raro;
- longitud promedio y percentiles de tokens por muestra;
- porcentaje de tokens desconocidos;
- reconstrucción de ida/vuelta.
El tokenizador se congela para una serie de experimentos. Si se cambia, versionar y volver a entrenar/convertir embeddings de forma explícita.

## 5. Formato conversacional recomendado
Una línea JSONL por conversación:
```json
{"messages":[{"role":"user","content":"¿Qué es la fotosíntesis?"},{"role":"assistant","content":"Es el proceso por el que plantas, algas y algunas bacterias convierten energía luminosa en energía química."}]}
{"messages":[{"role":"user","content":"¿Cuánto es 8 por 7?"},{"role":"assistant","content":"56."},{"role":"user","content":"¿Y si le sumo 4?"},{"role":"assistant","content":"60."}]}
```
Roles permitidos deben definirse y validarse. No mezclar formatos sin un convertidor probado. Añadir metadatos de fuente/curación fuera del texto de entrenamiento cuando corresponda.

## 6. Balance inicial del corpus
No fijar porcentajes definitivos antes de conocer capacidad y objetivo. Empezar con pequeños subconjuntos separados para:
1. texto español limpio;
2. diálogo de turnos cortos y largos;
3. instrucciones de tareas;
4. aclaración, incertidumbre y corrección;
5. pruebas de robustez.
Medir por categoría; aumentar únicamente la categoría con fallo confirmado. No repetir indefinidamente el mismo corpus para aparentar más tokens: puede producir memorización y sobreajuste.

## 7. Plantilla de auditoría de datos
Registrar total de documentos, bytes, tokens tras tokenización, duplicados removidos, idiomas, fuentes/licencias, longitud media/p95, particiones y fecha. El número de palabras no sustituye el conteo real de tokens del tokenizador.
