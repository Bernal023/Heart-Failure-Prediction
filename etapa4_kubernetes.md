# Etapa 4: orquestación con Kubernetes (Minikube)

## Objetivo

Docker ejecuta un contenedor; **Kubernetes** se encarga de mantenerlo funcionando y de exponerlo.
Describimos el estado deseado («quiero una réplica de esta imagen, accesible en este puerto») y
Kubernetes trabaja para que la realidad coincida con esa descripción: si el contenedor se cae, lo
vuelve a crear. En un entorno real esto se hace en un clúster de varias máquinas; aquí se usa
**Minikube**, un clúster de un solo nodo que corre en el computador local.

## Conceptos clave

| Término | Qué es | En este proyecto |
|---|---|---|
| Clúster / nodo | Conjunto de máquinas que ejecutan contenedores | Un único nodo creado por Minikube dentro de Docker |
| Pod | La unidad mínima desplegable: uno o más contenedores que comparten red | Un pod con el contenedor `heart-api` |
| Deployment | Declara cuántos pods deben existir y los recrea si fallan | `heart-model`, con 1 réplica |
| Service | Dirección de red estable para un conjunto de pods | `heart-service`, que balancea hacia los pods |
| Etiqueta (*label*) y selector | Mecanismo con el que un objeto encuentra a otros | El `Service` busca pods con `app: heart-model` |
| `kubectl` | Herramienta de línea de comandos para hablar con el clúster | Aplica los manifiestos y consulta el estado |

Relación entre los objetos:

```text
Cliente --> Service heart-service (puerto 80)
                |  selector: app = heart-model
                v
            Pod heart-model-xxxx (creado por el Deployment)
                |  contenedor heart-api, escucha en el puerto 8000
                v
            FastAPI + modelo
```

## Manifiestos

El `Deployment` declara que debe haber una réplica del contenedor `heart-api` escuchando en el
puerto 8000.

```{literalinclude} /k8s/deployment.yaml
:language: yaml
:linenos:
```

* `replicas: 1`: número de pods deseado. Subirlo a 3 haría que Kubernetes creara dos copias más.
* `selector.matchLabels` y `template.metadata.labels`: deben coincidir. Así el `Deployment` sabe
  qué pods le pertenecen.
* `containers`: nombre del contenedor, la imagen y el puerto. `containerPort: 8000` es
  informativo; indica qué puerto usa la aplicación.
* `imagePullPolicy: IfNotPresent`: usar la imagen local si ya está en el clúster, en lugar de
  intentar descargarla de internet.

El `Service` da una dirección estable a los pods con la etiqueta `app: heart-model`.

```{literalinclude} /k8s/service.yaml
:language: yaml
:linenos:
```

* `selector`: a qué pods enviar el tráfico (los que tienen `app: heart-model`).
* `port: 80`: puerto por el que se accede al servicio. `targetPort: 8000`: puerto del contenedor
  al que se redirige el tráfico. Quien llame al servicio no necesita saber en qué puerto escucha
  la aplicación.
* `type: LoadBalancer`: pide una IP externa. En la nube la asigna el proveedor; en Minikube no
  existe esa infraestructura (véase más abajo).

Respecto al ejemplo del enunciado, la imagen es `heart-api` (la construida localmente, sin
usuario de Docker Hub) y se añadió `imagePullPolicy: IfNotPresent`.

## Despliegue paso a paso

```bash
minikube start --driver=docker
minikube image load heart-api
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl get pods
kubectl get svc
minikube service heart-service
```

| Comando | Qué hace |
|---|---|
| `minikube start --driver=docker` | Crea el clúster local usando Docker como base |
| `minikube image load heart-api` | Copia la imagen local dentro del clúster |
| `kubectl apply -f ...` | Envía los manifiestos; Kubernetes crea o actualiza los objetos para que coincidan |
| `kubectl get pods` | Lista los pods; el estado debe pasar de `ContainerCreating` a `Running` |
| `kubectl get svc` | Lista los servicios y sus puertos |
| `minikube service heart-service` | Abre un túnel desde el computador hacia el servicio y muestra su URL |

### Por qué hay que cargar la imagen

Minikube tiene su **propio** motor de Docker, separado del que usa el computador. Una imagen
construida con `docker build` en el equipo no aparece sola dentro del clúster. Hay dos caminos:
subirla a un registro como Docker Hub, o copiarla con `minikube image load`. Se eligió el
segundo porque no requiere cuenta ni internet. Combinado con `imagePullPolicy: IfNotPresent`,
Kubernetes usa la imagen cargada y no intenta descargar `heart-api` de un registro donde no existe.

### Por qué `EXTERNAL-IP` queda pendiente

El `Service` de tipo `LoadBalancer` espera que el proveedor de nube le asigne una IP pública. Minikube
no la asigna, así que `kubectl get svc` muestra `<pending>` en `EXTERNAL-IP`. Es el comportamiento
normal en un clúster local y no es un error. Para acceder, `minikube service` abre un túnel local.

## Qué demuestra esta etapa

* El mismo contenedor que corrió con Docker funciona dentro de un clúster, descrito mediante
  archivos declarativos reproducibles (`kubectl apply -f k8s/`).
* El `Service` desacopla a los clientes de los pods: si el pod se recrea, la dirección del
  servicio no cambia.

Con una sola réplica en un solo nodo no se pone a prueba la alta disponibilidad ni el reparto de
carga; para eso habría que aumentar `replicas` (por ejemplo, con `kubectl scale`), cosa que no se
hizo en este proyecto.

## Evidencia

```{figure} /evidencias/kubectl_get_pods.png
:width: 95%
:name: fig-kubectl

Estado del pod (`Running`) y del servicio (`kubectl get pods` y `kubectl get svc`).
```

Predicción obtenida a través del servicio de Kubernetes, por el túnel de Minikube
(`127.0.0.1:53725`). La respuesta (0.9515, clase 1) es idéntica a la del contenedor Docker, como
corresponde: es el mismo modelo y la misma entrada.

```{figure} /evidencias/k8s_swagger.png
:width: 95%
:name: fig-k8s

Respuesta 200 de `POST /predict` servida por el clúster de Minikube.
```

```{note}
El puerto del túnel (53725) lo asigna Minikube en cada ejecución y la dirección `127.0.0.1` solo
existe en el computador donde corre el clúster. Esta URL no puede compartirse con otra persona;
para eso haría falta un clúster en la nube con una IP pública.
```

## Limpieza

Al terminar, `minikube stop` detiene el clúster y libera la memoria y el procesador que consume
junto con Docker; los despliegues se conservan para la próxima vez.
