# Etapa 6: monitoreo de deriva de datos con Evidently

La **deriva de datos** (*data drift*) ocurre cuando los datos que recibe un modelo dejan de
parecerse a los de entrenamiento; las predicciones pueden degradarse sin que aparezca ningún
error. Evidently compara dos conjuntos columna por columna con pruebas estadísticas.

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

## Resultados

* 11 columnas analizadas, **0 con deriva** (0.0 %). Evidently declara deriva del dataset cuando
  la proporción de columnas con deriva alcanza el umbral de 0.5.
* La columna «Drift Score» es el *p-value* de cada prueba (K-S para numéricas, *chi-square* o
  *Z-test* para categóricas). Con el umbral por defecto de Evidently, hay deriva en una columna
  cuando el *p-value* es menor que 0.05.

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

La variable más cercana al umbral es `Age` (p = 0.072), todavía por encima de 0.05.

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

```{warning}
Que no se detecte deriva aquí era lo esperable: `X_train` y `X_test` salen de la **misma**
partición aleatoria del mismo dataset, así que tienen la misma distribución por construcción. El
reporte demuestra el mecanismo de monitoreo, pero **no** demuestra que el modelo seguirá siendo
estable en producción. Para eso habría que comparar la referencia con los datos reales que
llegan a la API a lo largo del tiempo, y repetir el reporte periódicamente.
```
