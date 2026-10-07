# Etapa 6: monitoreo de deriva de datos con Evidently

## Objetivo

Un modelo no falla con un error visible cuando los datos cambian: sigue respondiendo, pero con
predicciones cada vez menos fiables. El monitoreo busca detectar ese cambio a tiempo. Esta etapa
genera un reporte que compara los datos de referencia (los de entrenamiento) con los datos
«actuales» y señala qué variables han cambiado de distribución.

## Conceptos clave

| Término | Qué significa |
|---|---|
| Deriva de datos (*data drift*) | Cambia la distribución de las variables de entrada respecto a la de entrenamiento |
| Deriva del concepto (*concept drift*) | Cambia la relación entre las variables y el objetivo, aunque las variables parezcan iguales |
| Datos de referencia | Con lo que se compara; normalmente, los datos de entrenamiento |
| Datos actuales | Lo que se quiere vigilar; en producción, las peticiones reales que recibe la API |

Evidently detecta la **deriva de datos**. La deriva del concepto solo puede medirse cuando se
conocen los resultados reales, comparando las predicciones con lo que ocurrió.

## Cómo se generó el reporte

Se compara `X_train` (referencia) con `X_test` (datos «actuales»). Se usa la API nueva de
Evidently (≥ 0.7) y, si no está disponible, la antigua que muestra el enunciado.

```python
DRIFT_PATH = BASE_DIR / "drift_report.html"

if DRIFT_PATH.exists() and not FORCE_RETRAIN:
    print("[SKIP] drift_report.html ya existe en Drive")
else:
    try:  # API nueva (evidently >= 0.7)
        from evidently import Report
        from evidently.presets import DataDriftPreset
        snapshot = Report([DataDriftPreset()]).run(
            current_data=X_test, reference_data=X_train)
        snapshot.save_html(str(DRIFT_PATH))
    except Exception as e_new:
        try:  # API antigua (evidently < 0.7)
            from evidently.report import Report
            from evidently.metric_preset import DataDriftPreset
            report = Report(metrics=[DataDriftPreset()])
            report.run(reference_data=X_train, current_data=X_test)
            report.save_html(str(DRIFT_PATH))
        except Exception as e_old:
            print("No se pudo generar el reporte de Evidently.")
            print("  API nueva:", repr(e_new)[:200])
            print("  API antigua:", repr(e_old)[:200])
    if DRIFT_PATH.exists():
        print("[SAVED] drift_report.html")
```

El reporte interactivo completo se guardó como `drift_report.html`:
<a href="drift_report.html">abrir el reporte de Evidently</a>.

## Cómo decide Evidently si hay deriva

Para cada columna aplica una prueba estadística que compara la distribución de referencia con la
actual y devuelve un *p-value*. El criterio depende del tipo de variable:

| Tipo de variable | Prueba | Idea |
|---|---|---|
| Numérica (`Age`, `RestingBP`, `Cholesterol`, `MaxHR`, `Oldpeak`) | Kolmogorov-Smirnov (K-S) | Compara las distribuciones acumuladas de los dos conjuntos |
| Categórica binaria (`Sex`, `FastingBS`, `ExerciseAngina`) | Z-test de proporciones | Compara la proporción de cada categoría |
| Categórica con más de dos categorías (`ChestPainType`, `RestingECG`, `ST_Slope`) | Chi-cuadrado | Compara las frecuencias de cada categoría |

Con el umbral por defecto de Evidently, hay deriva en una columna cuando el *p-value* es menor
que 0.05. A nivel de dataset, se declara deriva cuando la proporción de columnas con deriva
alcanza el umbral de 0.5.

## Resultados

* 11 columnas analizadas, **0 con deriva** (0.0 %); no se detectó deriva del dataset.
* La columna «Drift Score» del reporte es el *p-value* de cada prueba:

| Variable | Tipo | Prueba | p-value | ¿Deriva? |
|---|---|---|---|---|
| Sex | categórica | Z-test | 0.889914 | No |
| MaxHR | numérica | K-S | 0.608245 | No |
| RestingBP | numérica | K-S | 0.576959 | No |
| ExerciseAngina | categórica | Z-test | 0.572223 | No |
| FastingBS | categórica | Z-test | 0.544656 | No |
| RestingECG | categórica | chi-square | 0.517262 | No |
| Oldpeak | numérica | K-S | 0.322876 | No |
| ST_Slope | categórica | chi-square | 0.314917 | No |
| ChestPainType | categórica | chi-square | 0.198885 | No |
| Cholesterol | numérica | K-S | 0.171550 | No |
| Age | numérica | K-S | 0.072136 | No |

```{figure} /evidencias/drift_1_a_10.png
:width: 95%
:name: fig-drift-1

Resumen del reporte y primeras diez variables.
```

```{figure} /evidencias/drift_age.png
:width: 95%
:name: fig-drift-2

Variable restante (`Age`) en la segunda página de la tabla.
```

## Cómo interpretarlo

* Ninguna variable cruza el umbral. La más cercana es `Age` (p = 0.072), todavía por encima de
  0.05; los histogramas de referencia y actual de esa variable son visualmente parecidos.
* Con 11 pruebas al 5 %, aun entre dos muestras de la misma población cabría esperar, en promedio,
  alrededor de 0.55 falsas alarmas por azar. Que no haya ninguna es coherente con datos de
  origen común.

```{warning}
Que no se detecte deriva aquí era lo esperable: `X_train` y `X_test` salen de la **misma**
partición aleatoria del mismo dataset, así que tienen la misma distribución por construcción. El
reporte demuestra el mecanismo de monitoreo, pero **no** demuestra que el modelo seguirá siendo
estable en producción.
```

## Cómo se usaría en producción

1. Conservar los datos de entrenamiento como **referencia**.
2. Registrar las peticiones que llegan a `/predict` (las variables de entrada, sin datos
   personales innecesarios) y usarlas como datos **actuales**, por ventanas de tiempo.
3. Generar el reporte periódicamente y definir qué hacer si aparece deriva: investigar el origen
   del cambio, reentrenar o reemplazar el modelo.
4. Cuando se conozca el desenlace real de los pacientes, medir también el rendimiento (AUC,
   *recall*) para detectar deriva del concepto, que Evidently por sí solo no ve.

Una forma sencilla de comprobar que el monitoreo funciona, **no ejecutada en este proyecto**, es
modificar artificialmente los datos actuales (por ejemplo, sumar 15 años a `Age` en una copia de
`X_test`), repetir el reporte y verificar que `Age` aparezca con deriva.
