# Conclusiones

## Resultados

* Se construyó un flujo reproducible sin fuga de datos: la partición se hace antes de imputar y
  escalar, y ambos pasos viven dentro del `Pipeline`, de modo que se ajustan solo con
  entrenamiento en cada pliegue.
* Siete modelos se compararon con la misma validación cruzada estratificada de 5 pliegues. El
  modelo final, **Random Forest**, se eligió por AUC de validación cruzada (0.9317), y en prueba
  obtuvo AUC 0.9290, *accuracy* 0.8804 y *recall* 0.9216.
* El modelo se sirvió como API (FastAPI), se contenerizó (Docker), se desplegó en un clúster
  local (Minikube) y su código se verifica automáticamente (GitHub Actions). Se generó un reporte
  de deriva con Evidently.

## Limitaciones

* **Poca muestra de prueba.** Con 184 pacientes, los cuatro mejores modelos en prueba (KNN,
  regresión logística, Random Forest y Gradient Boosting) están separados por menos de 0.003 de
  AUC. No hay base para decir que Random Forest es mejor que la regresión logística; esta última
  es más simple y tuvo igual o mejor *accuracy* y *recall* en prueba.
* **Una sola partición.** Los resultados de prueba dependen de una única división 80/20. Repetir
  con varias particiones, o con validación cruzada anidada, daría una estimación más estable.
* **Demostración de fuga limitada.** La diferencia entre escalar antes y después de dividir
  (0.9298 frente a 0.9115) viene de una sola partición y no mide el tamaño real de la fuga.
* **Errores clínicos.** El modelo clasificó como sanos a 8 de 102 pacientes enfermos. No se
  ajustó el umbral de decisión para priorizar el *recall*.
* **Datos.** 172 colesteroles iguales a 0 son valores inválidos imputados con la mediana; las
  predicciones para pacientes sin colesterol registrado son menos fiables. Además, el dataset es
  una compilación pequeña y no representa necesariamente a otras poblaciones.
* **Monitoreo.** El reporte de Evidently compara dos partes del mismo dataset, por lo que no
  prueba estabilidad en producción (véase la Etapa 6).
* **Despliegue.** Minikube corre en un solo equipo con una réplica; la URL del servicio no es
  accesible desde fuera. El CI valida el código, no despliega ni mide la calidad del modelo.
* **API.** No valida los valores de entrada (por ejemplo, rangos de edad); categorías
  desconocidas se ignoran en la codificación *one-hot* y los campos faltantes se imputan.

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
6. **Este libro.** `jupyter-book build .` desde la raíz del proyecto.

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
