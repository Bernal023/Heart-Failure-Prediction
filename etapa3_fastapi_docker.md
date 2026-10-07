# Etapa 3: despliegue con FastAPI y Docker

## La API

`app/api.py` carga el modelo final y expone dos rutas:

* `GET /health`: responde `{"status": "ok"}`; sirve para comprobar que el servicio está vivo.
* `POST /predict`: recibe los datos de un paciente y devuelve la probabilidad de enfermedad y la
  clase predicha (1 si la probabilidad es mayor que 0.5).

```{literalinclude} /app/api.py
:language: python
:linenos:
```

El archivo `app/features.json` guarda la lista de columnas que el modelo espera. La API ordena
los datos recibidos según esa lista (`reindex`), por lo que un campo faltante llega como valor
nulo y el `Pipeline` lo imputa con la mediana (numéricas) o la moda (categóricas) de
entrenamiento.

## El contenedor

```{literalinclude} /docker/Dockerfile
:language: docker
:linenos:
```

```{literalinclude} /docker/requirements.txt
:language: text
```

Construcción y ejecución:

```bash
docker build -t heart-api -f docker/Dockerfile .
docker run -p 8000:8000 heart-api
```

## Diferencias respecto al ejemplo del enunciado

| Enunciado | Esta implementación | Motivo |
|---|---|---|
| `features: list` y `np.array(...).reshape(1, -1)` | `features: Dict[str, Any]` convertido a `DataFrame` | El `Pipeline` incluye un `ColumnTransformer` que trabaja con **nombres de columna**; una lista de números no sabría qué variable es cuál. |
| `python:3.10-slim` | Misma versión de Python que usó Colab (3.13) | Un modelo guardado con `joblib` debe cargarse en un entorno compatible con el que lo entrenó. |
| `scikit-learn` sin versión | `scikit-learn==1.6.1` | Misma razón: la versión debe coincidir con la del entrenamiento. |
| Solo `/predict` | Se agregó `/health` | Permite verificar el servicio sin enviar datos. |
| Cinco dependencias | Se agregaron `pandas` y `numpy` | La API construye un `DataFrame`. |

## Evidencia

Predicción desde la interfaz interactiva de FastAPI (`/docs`) en `localhost:8000`. El paciente
de ejemplo (`tests/sample_input.json`) recibe una probabilidad de enfermedad de 0.9515 y la
clase 1.

```{figure} /evidencias/docker_swagger.png
:width: 95%
:name: fig-docker

Respuesta 200 de `POST /predict` en el contenedor Docker.
```

```{note}
El valor `"Cholesterol": null` del ejemplo no es un error: representa un colesterol no
registrado (en el dataset aparece como 0), y el `Pipeline` lo reemplaza por la mediana de
entrenamiento antes de predecir.
```
