# Etapa 5: integración continua con GitHub Actions

Cada vez que se hace `git push`, GitHub levanta una máquina Ubuntu y ejecuta el flujo definido en
`.github/workflows/ci.yml`. Si algún paso falla, el *commit* queda marcado con una ✗ roja.

```{literalinclude} /.github/workflows/ci.yml
:language: yaml
:linenos:
```

## Qué verifica

1. **Descarga el código** y **prepara Python** con la misma versión usada en el entrenamiento.
2. **Instala dependencias** desde `docker/requirements.txt` (con las mismas versiones que en el
   contenedor) más `flake8`, `pytest` y `httpx`.
3. **Lint:** `flake8 app/` revisa el estilo (PEP 8) del código de la API.
4. **Pruebas:** `python -m pytest tests/` ejecuta las pruebas de `tests/test_api.py`.

```{literalinclude} /tests/test_api.py
:language: python
:linenos:
```

Las pruebas cargan el modelo real (`app/model.joblib`, por eso se versiona) y comprueban que
`/health` responde `ok` y que `/predict` devuelve una probabilidad entre 0 y 1 y una clase 0 o 1,
usando el paciente de `tests/sample_input.json`.

Se ejecuta `python -m pytest` y no `pytest` a secas, junto con un `pytest.ini` que añade la
raíz del proyecto a la ruta de importación, para que `from app.api import app` funcione desde la
carpeta raíz.

## Qué no hace

Este flujo es de **integración** continua: valida el código, pero no construye la imagen de
Docker ni despliega nada (no es *entrega* continua). Tampoco comprueba la calidad del modelo,
solo que la API lo cargue y responda.

## Evidencia

Repositorio: <https://github.com/Bernal023/Heart-Failure-Prediction/actions>

```{figure} /evidencias/github_actions.png
:width: 95%
:name: fig-actions

Ejecución del workflow CI en la pestaña Actions de GitHub.
```
