# 06 — Currículo de matemáticas, cálculo y diagramas

## Objetivo
Desarrollar la capacidad de explicar conceptos, resolver ejercicios paso a paso, comprobar resultados y representar relaciones matemáticas. Separar lo que resuelve la red de lo que verifica una herramienta externa.

## 1. Ruta progresiva de todas las ramas principales

### Aritmética y sentido numérico
Valor posicional; suma, resta, multiplicación, división; operaciones combinadas; acarreo y préstamo; fracciones; decimales; porcentajes; razones y proporciones; potencias, raíces, estimación y unidades.

### Preálgebra y álgebra
Variables y expresiones; simplificación; ecuaciones e inecuaciones; sistemas lineales; polinomios; productos notables; factorización; exponentes y radicales; ecuaciones cuadráticas; funciones, dominio, rango, composición e inversa.

### Geometría y geometría analítica
Puntos, rectas, ángulos, triángulos, polígonos y circunferencia; perímetro, área y volumen; semejanza y congruencia; Pitágoras; coordenadas, pendiente, distancia y ecuación de recta.

### Trigonometría y precálculo
Seno, coseno, tangente, identidades y resolución de triángulos; funciones y gráficas; transformaciones; sucesiones; límites y continuidad.

### Cálculo diferencial
Concepto de derivada; interpretación como pendiente y tasa de cambio; reglas de potencia, suma, producto, cociente y cadena; derivación implícita; derivadas trigonométricas, exponenciales y logarítmicas; optimización y análisis de crecimiento.

### Cálculo integral y multivariable
Antiderivadas e integral definida; teorema fundamental del cálculo; sustitución e integración por partes; áreas y acumulación; derivadas parciales, gradiente e integrales múltiples como contenidos avanzados.

### Probabilidad y estadística
Conteo; probabilidad condicional; independencia; variables aleatorias y distribuciones; media, mediana, varianza y desviación estándar; muestreo; intervalos de confianza; pruebas de hipótesis; correlación y regresión; incertidumbre y diferencia entre correlación y causalidad.

### Álgebra lineal
Vectores y matrices; sistemas lineales; determinantes; transformaciones; espacios vectoriales; independencia lineal, bases y valores propios.

### Matemática discreta y lógica
Lógica proposicional; conjuntos; relaciones; combinatoria; grafos; inducción; recursión; algoritmos y complejidad básica.

### Demostraciones
Definiciones, hipótesis y tesis; contraejemplos; demostración directa, por contradicción, contraposición e inducción. La IA debe justificar por qué un procedimiento es válido.

## 2. Tres modos de cálculo que debe distinguir

1. **Simbólico:** manipular expresiones y producir resultados exactos. Ejemplo: si f(x)=x^3+2x, entonces f'(x)=3x^2.
2. **Numérico:** producir aproximaciones indicando precisión y tolerancia. Una aproximación no debe presentarse como resultado exacto.
3. **Verificado con herramienta:** usar una calculadora o sistema algebraico y registrar claramente qué calculó la red y qué comprobó la herramienta. No atribuir a la red el trabajo externo.

## 3. Cómo enseñar cada concepto
Cada unidad debe incluir: explicación conceptual, ejemplos resueltos, procedimiento paso a paso, errores frecuentes, ejercicios graduados, problemas verbales y variantes nuevas. El modelo debe aprender a detectar datos insuficientes, pedir aclaraciones y comprobar la respuesta por un método independiente cuando sea posible.

## 4. Diagramas y gráficas
Capacidades a entrenar y evaluar:
- recta numérica y plano cartesiano;
- gráficas de funciones y curvas;
- triángulos, ángulos, figuras y sólidos;
- diagramas de flujo de algoritmos;
- árboles, grafos y relaciones;
- esquemas de pasos para resolver problemas y demostrar resultados.

Para diagramas estructurados se puede usar Mermaid. Para gráficas matemáticas se deben generar datos y ejes correctos y renderizarlos con una herramienta; no basta con producir una imagen atractiva. Validar etiquetas, unidades, conexiones y correspondencia con el enunciado.

## 5. Evaluación
Medir por separado:
- exactitud de la respuesta;
- validez de cada paso;
- explicación conceptual;
- detección y corrección de errores;
- transferencia a ejercicios nuevos;
- elección correcta de método simbólico, numérico o herramienta;
- sintaxis y fidelidad del diagrama;
- capacidad de reconocer incertidumbre.

Separar train, validation y test por problema/fuente. Mantener test sellado y no usar sus respuestas para entrenar. Informar resultados por rama y nivel, no solo un promedio general.

## 6. Puertas de avance
No pasar a derivadas hasta que álgebra, funciones y manipulación de expresiones estén suficientemente dominadas. No pasar a integrales hasta evaluar límites, continuidad y derivadas. Los umbrales se fijan después de medir el baseline; no inventar porcentajes de aprobación antes de tener datos.

## 7. Límite realista
“Todas las matemáticas” representa un programa extenso y continuo. Este currículo establece una ruta amplia desde fundamentos hasta contenidos universitarios seleccionados; no implica que leer libros o completar una sola fase garantice dominio matemático general.
