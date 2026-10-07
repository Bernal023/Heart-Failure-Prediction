# Conclusiones

## Resumen por etapa

| Etapa | Qué se logró | Qué se aprendió |
|---|---|---|
| 0 y 1 | Estructura del proyecto, limpieza de valores inválidos, partición estratificada 80/20 antes de transformar | Los ceros de `Cholesterol` (172) y de `RestingBP` (1) son valores imposibles que hay que tratar como faltantes; la partición debe ir antes de cualquier transformación |
| 1 | Demostración de fuga de datos | El `Pipeline` evita la fuga del preprocesamiento, pero no la del **objetivo**: una variable construida con la respuesta da AUC 1.0 con cualquier flujo |
| 2 | Siete modelos en `Pipeline` + `GridSearchCV`, ranking, evaluación y *checkpointing* | Con pocos datos tabulares, modelos simples y complejos rinden de forma parecida; elegir por validación cruzada evita usar la prueba para decidir |
| 3 | API con FastAPI y contenedor Docker | Serializar el `Pipeline` completo evita reimplementar el preprocesamiento; la versión de Python y de scikit-learn deben coincidir con las del entrenamiento |
| 4 | Despliegue declarativo en Kubernetes local | Pod, Deployment y Service cumplen funciones distintas; la imagen local debe cargarse en el clúster |
| 5 | Verificación automática en cada `push` | El CI detecta errores de entorno que en el computador propio pasan inadvertidos |
| 6 | Reporte de deriva con Evidently | Sin datos reales de producción, el reporte solo demuestra el mecanismo |

## Análisis de los resultados del modelo

* **Rendimiento.** Random Forest, elegido por AUC de validación cruzada (0.9317), obtuvo en
  prueba AUC 0.9290, *accuracy* 0.8804, *precision* 0.8704 y *recall* 0.9216. Clasificó
  correctamente a 94 de 102 pacientes con enfermedad y a 68 de 82 sanos.
* **Los modelos no se distinguen entre sí.** En prueba, KNN (0.9313), regresión logística
  (0.9309), Random Forest (0.9290) y Gradient Boosting (0.9287) están separados por menos de 0.003
  de AUC. Con 184 pacientes de prueba, una diferencia tan pequeña no permite concluir que un
  modelo sea mejor que otro (no se calcularon intervalos de confianza). La regresión logística, mucho más simple, tuvo la mejor *accuracy* (0.8967) y el mejor
  *recall* (0.9314). Una explicación plausible, que este proyecto no verificó, es que en un
  dataset pequeño y de pocas variables hay poco que ganar con modelos más complejos.
* **Estimación optimista de la validación cruzada.** El AUC de validación cruzada de Random Forest
  (0.9317) es algo mayor que el de prueba (0.9290). Es coherente con lo esperado: ese número se
  usó para elegir hiperparámetros y modelo, de modo que tiende a ser optimista. Con una diferencia
  tan pequeña no puede afirmarse que se deba solo a eso. La cifra de prueba, que no intervino en
  ninguna decisión, es la estimación más honesta.
* **Tipo de error.** Ocho pacientes con enfermedad fueron clasificados como sanos (7.8 % de los
  enfermos). En un contexto clínico es el error más costoso, y el umbral de 0.5 usado no se
  ajustó para priorizarlo.

## Limitaciones

| Ámbito | Limitación |
|---|---|
| Evaluación | Una sola partición de prueba con 184 pacientes; no se calcularon intervalos de confianza para las métricas |
| Fuga de datos | La diferencia entre escalar antes y después de dividir (0.9298 frente a 0.9115) viene de una sola partición y no mide el tamaño real de la fuga |
| Datos | 172 colesteroles inválidos imputados con la mediana; las predicciones para pacientes sin colesterol registrado son menos fiables. El dataset es una compilación pequeña y no representa necesariamente a otras poblaciones |
| API | No valida tipos ni rangos de las variables; sin autenticación; un solo proceso |
| Docker y Kubernetes | Una réplica en un solo nodo local; el modelo va dentro de la imagen; la URL de Minikube no es accesible desde fuera |
| CI | Valida el código, no despliega ni mide la calidad del modelo; solo revisa el estilo de `app/` |
| Monitoreo | El reporte compara dos partes del mismo dataset, por lo que no prueba estabilidad en producción |
| Uso clínico | El modelo es un ejercicio académico y no una herramienta de diagnóstico |

## Mejoras posibles

| Mejora | Por qué | Cómo |
|---|---|---|
| Evaluación más robusta | Reducir la dependencia de una sola partición | Validación cruzada repetida o anidada, e intervalos de confianza por *bootstrap* para el AUC |
| Ajustar el umbral de decisión | Reducir falsos negativos | Elegir el umbral con la curva precisión-*recall* sobre datos de validación (nunca sobre la prueba) |
| Calibrar las probabilidades | Que una probabilidad de 0.9 signifique realmente ~90 % de riesgo | Calibración con `CalibratedClassifierCV` y revisión de curvas de calibración |
| Validar la entrada de la API | Rechazar datos imposibles en lugar de predecir sobre ellos | Modelos de Pydantic con tipos, categorías permitidas y rangos |
| Entrega continua | Automatizar la construcción de la imagen | Añadir al workflow la construcción de la imagen Docker y su publicación en un registro |
| Más réplicas y comprobaciones de salud | Disponibilidad y recuperación | `replicas` mayores y sondas `livenessProbe`/`readinessProbe` apuntando a `/health` |
| Monitoreo real | Detectar cambios en producción | Registrar las peticiones a `/predict` y compararlas con la referencia por ventanas de tiempo; medir rendimiento cuando haya desenlaces reales |
| Versionado de modelos | Trazabilidad | Un registro de modelos (por ejemplo, MLflow) con métricas y versiones |

## Reproducción

1. **Datos y modelos (Colab).** Ejecutar los notebooks en Colab con la carpeta
   `/content/drive/MyDrive/Heart_Failure_Prediction`. `heart.csv` se toma de Drive o se descarga
   de Kaggle. Gracias al *checkpointing*, repetir la ejecución solo reentrena los modelos que
   falten.
2. **API local.**

   ```bash
   pip install -r docker/requirements.txt
   uvicorn app.api:app --reload
   ```

3. **Contenedor.** `docker build -t heart-api -f docker/Dockerfile .` y
   `docker run -p 8000:8000 heart-api`.
4. **Kubernetes.** `minikube start --driver=docker`, `minikube image load heart-api` y
   `kubectl apply -f k8s/`.
5. **Pruebas y estilo.** `flake8 app/` y `python -m pytest tests/`.
6. **Este libro.** Se compila con `jupyter-book build .` desde la raíz del proyecto, o se
   publica automáticamente con GitHub Actions.

## Problemas y decisiones para evitarlos

| Problema | Origen | Causa | Solución |
|---|---|---|---|
| `flake8 app/` falló con `E902` | Ocurrió | Se ejecutó desde la carpeta equivocada | Ejecutarlo desde la raíz del proyecto |
| `minikube` no se reconocía tras instalarlo | Ocurrió | La terminal no conocía la ruta nueva en el `PATH` | Reiniciar VS Code |
| Versión de Python del `Dockerfile` y del CI incompatible con `scikit-learn==1.6.1` | Anticipado | El ejemplo del enunciado usa Python 3.10 y el entrenamiento se hizo en Python 3.13 | Alinear ambas versiones con la de Colab antes de construir |
| `pytest tests/` podía no encontrar el paquete `app` | Anticipado | Con `pytest` a secas, la raíz del proyecto puede no estar en la ruta de importación | `python -m pytest` y `pytest.ini` con `pythonpath = .` |
| La API del enunciado recibe una lista de números | Anticipado | El `Pipeline` necesita nombres de columna | La API recibe un diccionario y construye un `DataFrame` |

## Cumplimiento del enunciado

| Etapa | Entregable pedido | Dónde está |
|---|---|---|
| 0 | Estructura de carpetas | Notebook 1 y estructura de la introducción |
| 1 | Exploración, nulos, evitar fuga de datos | Notebook 1 |
| 2 | Pipeline + `GridSearchCV`, ranking por AUC y *accuracy*, matriz de confusión, ROC y AUC | Notebook 2 |
| 3 | `app/api.py`, `Dockerfile`, `requirements.txt` | Etapa 3 |
| 4 | `deployment.yaml` y `service.yaml` | Etapa 4 |
| 5 | `ci.yml` con lint y pruebas | Etapa 5 |
| 6 | `drift_report.html` con Evidently | Etapa 6 |
