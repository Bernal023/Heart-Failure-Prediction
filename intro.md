# Predicción de falla cardíaca con Pipelines y MLOps local

**Materia:** Machine Learning  
**Autores:** Mateo Bernal y Jassan Arteta  
**Repositorio:** <https://github.com/TU_USUARIO/TU_REPO>

## Contexto

Las enfermedades cardiovasculares son la principal causa de muerte en el mundo según la OMS, y
detectarlas a tiempo es clave para evitar complicaciones graves. Este proyecto usa el dataset
*Heart Failure Prediction* de Kaggle (918 pacientes, 11 variables clínicas) para construir un
clasificador binario que estima si un paciente está en riesgo (`HeartDisease` = 1 o 0).

El objetivo no es solo entrenar un modelo, sino recorrer el ciclo completo de un modelo en
producción, de forma local: preprocesar sin fuga de datos, entrenar con validación segura,
servir el modelo como API, contenerizarlo, desplegarlo en Kubernetes, automatizar su
verificación y monitorear la deriva de los datos.

```{note}
Este proyecto es un ejercicio académico. El modelo no es una herramienta de diagnóstico y no
debe usarse para tomar decisiones médicas.
```

## Etapas y dónde encontrarlas

| Etapa | Qué se hizo | Herramienta | Capítulo |
|---|---|---|---|
| 0 | Estructura de carpetas, configuración en Drive | Google Colab | Notebook 1 |
| 1 | Limpieza, partición antes del escalado, demostración de *data leakage* | scikit-learn | Notebook 1 |
| 2 | Siete modelos con `Pipeline` + `GridSearchCV`, ranking, evaluación | scikit-learn | Notebook 2 |
| 3 | API REST y contenedor | FastAPI, Docker | Etapa 3 |
| 4 | Despliegue local en un clúster | Kubernetes (Minikube) | Etapa 4 |
| 5 | Lint y pruebas automáticas en cada `push` | GitHub Actions | Etapa 5 |
| 6 | Reporte de deriva de datos | Evidently | Etapa 6 |

## Resultado principal

Modelo final: **Random Forest** (elegido por AUC en validación cruzada de 5 pliegues).

| Métrica | Valor |
|---|---|
| AUC en validación cruzada | 0.9317 |
| AUC en prueba (184 pacientes) | 0.9290 |
| Accuracy en prueba | 0.8804 |
| Precision / Recall / F1 en prueba | 0.8704 / 0.9216 / 0.8952 |

Los detalles, y por qué las diferencias entre los mejores modelos no permiten declarar un
ganador claro, están en el Notebook 2 y en las conclusiones.

## Cómo leer este libro

* Los **notebooks 1 y 2** conservan las salidas de la ejecución real en Google Colab.
* Los capítulos de las **Etapas 3 a 6** muestran los archivos reales del proyecto (se incluyen
  directamente desde sus carpetas) y las capturas de la ejecución.
* Las **conclusiones** resumen los resultados, las limitaciones y cómo reproducir todo.

## Estructura del proyecto

```text
Heart_Failure_Prediction/
├── app/                      API (api.py), modelo y lista de variables
├── docker/                   Dockerfile y requirements.txt
├── k8s/                      deployment.yaml y service.yaml
├── notebooks/                notebooks 1 y 2 (y el notebook completo de Colab)
├── tests/                    pruebas de la API
├── .github/workflows/        ci.yml
├── models/ y results/        un archivo por modelo entrenado (checkpoints)
├── figures/                  curvas ROC y matriz de confusión
├── evidencias/               capturas usadas en este libro
├── drift_report.html         reporte de Evidently
├── model.joblib              modelo final
└── README.md
```
