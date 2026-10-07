# Etapa 5: integración continua con GitHub Actions

## Objetivo

Cuando varias personas modifican un proyecto, o una misma persona lo hace durante semanas, es
fácil romper algo sin darse cuenta. La **integración continua** (CI) automatiza la verificación:
cada vez que se sube código a GitHub, un servidor ejecuta las mismas comprobaciones, siempre en
un entorno limpio, y avisa si algo falla. Así el aviso llega al instante y no cuando alguien
intenta usar el proyecto semanas después.

## Conceptos clave

| Término | Qué es | En este proyecto |
|---|---|---|
| Workflow | Flujo automatizado definido en un archivo YAML dentro de `.github/workflows/` | `ci.yml` |
| Evento (*trigger*) | Lo que dispara el flujo | `on: [push]`: cada `git push` |
| Job | Conjunto de pasos que se ejecutan en una misma máquina | `build` |
| Runner | La máquina virtual temporal donde corre el job | `ubuntu-latest` |
| Step | Una acción o un comando dentro del job | Descargar, instalar, lint, pruebas |
| Linting | Revisión automática de estilo y errores simples del código | `flake8` |
| Prueba unitaria | Código que comprueba que una parte del programa se comporta como se espera | `pytest` |

## El workflow

```{literalinclude} /.github/workflows/ci.yml
:language: yaml
:linenos:
```

Paso a paso:

1. **`actions/checkout`** descarga el código del repositorio en el runner, que empieza vacío.
2. **`actions/setup-python`** instala Python con la misma versión usada para entrenar el modelo
   (3.13); es lo que permite instalar el `scikit-learn==1.6.1` que fija el `requirements.txt`.
3. **Instalar dependencias.** Se reutiliza `docker/requirements.txt`, de modo que el CI prueba
   con las mismas librerías y versiones que el contenedor. Se añaden `flake8` y `pytest`, que
   solo hacen falta para verificar, y `httpx`, que necesita el cliente de pruebas de FastAPI.
4. **Lint.** `flake8 app/` revisa el código de la API: errores de sintaxis, importaciones sin
   usar, líneas de más de 79 caracteres y otras reglas de estilo (PEP 8).
5. **Pruebas.** `python -m pytest tests/` ejecuta las pruebas de la API.

Si un paso falla, los siguientes no se ejecutan y el *commit* queda marcado con una ✗ roja.

## Las pruebas

```{literalinclude} /tests/test_api.py
:language: python
:linenos:
```

* **`test_health`** comprueba que `/health` responde `{"status": "ok"}`.
* **`test_predict`** envía a `/predict` el paciente de `tests/sample_input.json` y comprueba que
  la respuesta tiene código 200, que la probabilidad está entre 0 y 1 y que la clase es 0 o 1.
* Se usa `TestClient` de FastAPI, que ejecuta la aplicación **dentro del mismo proceso de la
  prueba**, sin levantar un servidor ni abrir puertos. Es rápido y funciona en el runner.
* Las pruebas cargan el modelo real, por eso `app/model.joblib` se versiona en el repositorio.
  Comprueban que la API carga el modelo y responde con el formato correcto; **no** comprueban
  que el modelo sea bueno.

## Archivos de apoyo

| Archivo | Para qué sirve |
|---|---|
| `pytest.ini` | Añade la raíz del proyecto a la ruta de importación (`pythonpath = .`) para que `from app.api import app` funcione al ejecutar desde la raíz |
| `.gitignore` | Evita subir credenciales (`kaggle.json`), el entorno virtual y carpetas pesadas (`models/`, `results/`, `figures/`) |
| `.dockerignore` | Excluye archivos innecesarios del contexto de construcción de Docker |

## Probar localmente antes de subir

Los mismos comandos del CI se pueden ejecutar en el computador, y conviene hacerlo antes del
`push` para no esperar al servidor:

```bash
flake8 app/
python -m pytest tests/
```

`flake8` no imprime nada cuando el código está bien, y `pytest` muestra el número de pruebas
aprobadas.

## Decisiones y diferencias respecto al enunciado

| Enunciado | Esta implementación | Motivo |
|---|---|---|
| `python-version: '3.10'` | La misma versión que Colab (3.13) | `scikit-learn==1.6.1` debe poder instalarse y leer el modelo guardado |
| `pytest tests/` | `python -m pytest tests/` más `pytest.ini` | Con `pytest` a secas el paquete `app` puede no encontrarse al importar |
| `pip install flake8 pytest` | Se añade `httpx` | `TestClient` de FastAPI lo necesita |
| `actions/checkout@v3`, `setup-python@v4` | `@v4` y `@v5` | Versiones más recientes de las acciones |

## Problemas encontrados

| Problema | Causa | Solución |
|---|---|---|
| `flake8 app/` falló con `E902 FileNotFoundError: 'app/'` | El comando se ejecutó desde `C:\proyectos` y no desde la carpeta del proyecto, donde está `app/` | Entrar a `Heart_Failure_Prediction` (o abrir esa carpeta en VS Code) y repetir el comando |

## Qué no hace este flujo

* Es de **integración** continua: valida el código, pero no construye la imagen de Docker, no la
  publica ni despliega nada. Eso sería *entrega* o *despliegue* continuo.
* No evalúa la calidad del modelo (no vuelve a entrenarlo ni compara métricas).
* Solo revisa el estilo de `app/`, no el de los notebooks ni el de las pruebas.

## Evidencia

Repositorio: <https://github.com/Bernal023/Heart-Failure-Prediction>

```{figure} /evidencias/github_actions.png
:width: 95%
:name: fig-actions

Ejecución del workflow CI en la pestaña Actions de GitHub.
```

## Publicación de este libro

Este mismo libro se compila y publica con otro workflow (`book.yml`) cada vez que se hace `push`
a la rama principal. Es independiente del CI de la API: uno verifica el código, el otro genera
y publica la documentación en GitHub Pages.
