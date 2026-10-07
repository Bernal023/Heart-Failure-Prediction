# Etapa 3: despliegue con FastAPI y Docker

## Objetivo

Un modelo guardado en un archivo no le sirve a nadie mientras solo pueda usarse desde un
notebook. Esta etapa convierte el modelo final en un **servicio**: un programa que está siempre
disponible, recibe por la red los datos de un paciente y responde con una predicción. Después se
empaqueta en un **contenedor** para que funcione igual en cualquier computador, sin depender de
qué versión de Python o de qué librerías tenga instaladas.

## Conceptos clave

| Término | Qué es | Papel en este proyecto |
|---|---|---|
| API REST | Interfaz con la que un programa le pide cosas a otro mediante peticiones HTTP | Permite que un navegador, una aplicación o otro servidor use el modelo sin conocer Python |
| Endpoint | Una dirección concreta de la API, asociada a una función | `/health` y `/predict` |
| JSON | Formato de texto para intercambiar datos | Entrada (datos del paciente) y salida (probabilidad y clase) |
| FastAPI | Librería de Python para construir APIs | Define los endpoints, valida la entrada y genera la documentación interactiva en `/docs` |
| Pydantic | Librería de validación de datos que usa FastAPI | La clase `Input` exige que la petición traiga un campo `features` con un diccionario |
| Uvicorn | Servidor que ejecuta la aplicación y atiende las peticiones | Es el comando con el que arranca el contenedor |
| Imagen | Plantilla inmutable con sistema base, Python, librerías y código | Se construye una vez con `docker build` |
| Contenedor | Una ejecución de una imagen, aislada del resto del sistema | Se crea con `docker run` |

## Del notebook a la API: qué se exporta

Al final del notebook 2 se guardan tres archivos que usa esta etapa:

* **`app/model.joblib`** (con una copia en la raíz): el `Pipeline` completo ya entrenado, es
  decir, imputación, escalado, codificación *one-hot* y Random Forest, todo en un solo objeto.
* **`app/features.json`**: lista ordenada de las columnas que el modelo espera, junto con el
  nombre del modelo y la versión de scikit-learn con la que se entrenó.
* **`tests/sample_input.json`**: un paciente de ejemplo, usado para probar la API a mano y en las
  pruebas automáticas.

Se serializa el `Pipeline` entero y no solo el bosque aleatorio. Así la API aplica
**exactamente** el mismo preprocesamiento que se usó al entrenar, sin reescribirlo. Reimplementar
a mano el escalado o la codificación en la API es una fuente clásica de errores silenciosos: si
difiere en algo, el modelo recibe datos distintos a los que conoce y las predicciones se
deterioran sin que aparezca ningún error.

## La API

```{literalinclude} /app/api.py
:language: python
:linenos:
```

Recorrido del código:

* **Carga al inicio.** `joblib.load` se ejecuta una sola vez cuando arranca el servicio, no en
  cada petición; leer el modelo del disco en cada llamada sería lento.
* **`FEATURES`.** Se lee de `features.json` para conocer las columnas y su orden.
* **`Input`.** Declara que el cuerpo de la petición debe tener un campo `features` que sea un
  diccionario. FastAPI rechaza automáticamente (código 422) las peticiones que no cumplan esto.
* **`GET /health`.** Responde `{"status": "ok"}`. Sirve para saber si el servicio está vivo sin
  enviar datos; es el tipo de ruta que consultan los sistemas de monitoreo.
* **`POST /predict`.** Convierte el diccionario en un `DataFrame` de una fila, lo ordena con
  `reindex(columns=FEATURES)`, pide la probabilidad de la clase 1 con `predict_proba` y devuelve
  esa probabilidad más la clase (1 si es mayor que 0.5).

Flujo de una petición:

```text
Cliente --JSON--> POST /predict --> Pydantic valida el cuerpo --> DataFrame de 1 fila
   --> reindex(FEATURES) --> Pipeline: imputar -> escalar / one-hot -> Random Forest
   --> probabilidad --> {"heart_disease_probability": ..., "prediction": 0 o 1}
```

### Contrato de la API

Petición (el paciente de `tests/sample_input.json`):

```json
{"features": {"Age": 46, "Sex": "M", "ChestPainType": "ASY", "RestingBP": 115.0,
              "Cholesterol": null, "FastingBS": 0, "RestingECG": "Normal",
              "MaxHR": 113, "ExerciseAngina": "Y", "Oldpeak": 1.5, "ST_Slope": "Flat"}}
```

Respuesta (valor obtenido en la ejecución, ver la evidencia más abajo):

```json
{"heart_disease_probability": 0.9515427868180606, "prediction": 1}
```

### Cómo reacciona ante entradas inusuales

| Situación | Qué ocurre | Por qué |
|---|---|---|
| Falta una variable o su valor es `null` (como `Cholesterol` en el ejemplo) | Se imputa con la mediana (numéricas) o la moda (categóricas) de entrenamiento | `reindex` crea un valor nulo y el `SimpleImputer` del `Pipeline` lo rellena |
| Una variable categórica trae una categoría que no existía en el entrenamiento | La categoría se ignora (todas sus columnas *one-hot* quedan en 0) | El codificador se creó con `handle_unknown="ignore"` |
| Falta el campo `features` o no es un diccionario | La API responde 422 | Validación de Pydantic |
| Una variable trae un tipo incorrecto (por ejemplo, texto en `Age`) | No se valida; se espera que el `Pipeline` falle y la API responda con error 500 (no se probó) | La API solo valida que `features` sea un diccionario |
| Un valor fuera de rango (por ejemplo, una edad de 300) | Se acepta y se predice | No hay validación de rangos |

Las dos últimas filas son limitaciones reales de esta versión, recogidas en las conclusiones.

## El contenedor

```{literalinclude} /docker/Dockerfile
:language: docker
:linenos:
```

```{literalinclude} /docker/requirements.txt
:language: text
```

| Instrucción | Qué hace |
|---|---|
| `FROM python:3.13-slim` | Parte de una imagen oficial con Python 3.13 y lo mínimo del sistema (variante *slim*, más liviana) |
| `WORKDIR /app` | Define la carpeta de trabajo dentro del contenedor |
| `COPY docker/requirements.txt .` | Copia primero solo la lista de dependencias |
| `RUN pip install --no-cache-dir -r requirements.txt` | Instala las librerías; `--no-cache-dir` evita guardar archivos temporales y reduce el tamaño de la imagen |
| `COPY app/ ./app/` | Copia el código de la API, el modelo y `features.json` |
| `CMD [...uvicorn...]` | Comando que se ejecuta al iniciar el contenedor: levanta la API en el puerto 8000 |

Detalles de diseño:

* **Orden de las capas.** Docker guarda en caché cada instrucción. Como las dependencias casi
  nunca cambian y el código sí, se copian y se instalan **antes** que `app/`: al modificar
  `api.py`, Docker reutiliza la capa de las librerías y la reconstrucción es mucho más rápida.
* **`--host 0.0.0.0`.** Dentro del contenedor, escuchar solo en `127.0.0.1` haría la API
  inaccesible desde fuera. `0.0.0.0` hace que atienda en todas las interfaces del contenedor.
* **Versiones fijas.** El `requirements.txt` fija `scikit-learn==1.6.1`, la versión con la que se
  entrenó el modelo, porque un archivo `joblib` solo se garantiza compatible con la misma versión.
* **`.dockerignore`.** Excluye `.venv`, `.git`, `models`, `results` y `figures` del contexto de
  construcción para que `docker build` no envíe archivos inútiles al motor de Docker.

Construcción y ejecución:

```bash
docker build -t heart-api -f docker/Dockerfile .
docker run -p 8000:8000 heart-api
```

* `-t heart-api` pone nombre a la imagen; `-f docker/Dockerfile` indica qué Dockerfile usar; el
  punto final es el **contexto** (la carpeta raíz del proyecto, de donde `COPY` toma los archivos).
* `-p 8000:8000` conecta el puerto 8000 del computador con el 8000 del contenedor.

## Cómo se verificó

1. Con el contenedor en marcha, abrir `http://localhost:8000/docs`, la documentación interactiva
   que FastAPI genera sola a partir del código.
2. Probar `POST /predict` con el paciente de ejemplo y comprobar que responde 200 con una
   probabilidad entre 0 y 1.
3. Comprobar `GET /health`.

## Diferencias respecto al ejemplo del enunciado

| Enunciado | Esta implementación | Motivo |
|---|---|---|
| `features: list` y `np.array(...).reshape(1, -1)` | `features: Dict[str, Any]` convertido a `DataFrame` | El `Pipeline` incluye un `ColumnTransformer` que trabaja con **nombres de columna**; una lista de números no sabría qué variable es cuál |
| `python:3.10-slim` | Misma versión de Python que usó Colab (3.13) | Un modelo guardado con `joblib` debe cargarse en un entorno compatible con el que lo entrenó |
| `scikit-learn` sin versión | `scikit-learn==1.6.1` | Misma razón: la versión debe coincidir con la del entrenamiento |
| Solo `/predict` | Se agregó `/health` | Permite verificar el servicio sin enviar datos |
| Cinco dependencias | Se agregaron `pandas` y `numpy` | La API construye un `DataFrame` |
| `joblib.load("app/model.joblib")` (ruta relativa al directorio de trabajo) | La ruta se calcula desde la ubicación de `api.py` | La API funciona igual se ejecute desde la raíz, desde el contenedor o desde las pruebas |

La versión de Python se alineó con la de Colab **antes** de construir la imagen, para no descubrir
la incompatibilidad durante el `docker build`: versiones recientes de scikit-learn no se instalan
en Python 3.10.

## Evidencia

Predicción desde la interfaz interactiva de FastAPI (`/docs`) en `localhost:8000`. El paciente
de ejemplo recibe una probabilidad de enfermedad de 0.9515 y la clase 1.

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

## Limitaciones de esta etapa

* No hay autenticación: cualquiera que alcance el puerto puede usar la API.
* La validación de entrada es mínima (véase la tabla de entradas inusuales).
* El modelo va dentro de la imagen; cambiar de modelo obliga a reconstruir la imagen.
* Un solo proceso de Uvicorn: suficiente para una demostración, no para mucho tráfico.
