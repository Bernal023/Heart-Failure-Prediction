# Etapa 4: orquestación con Kubernetes (Minikube)

Docker ejecuta un contenedor; Kubernetes se encarga de mantenerlo en ejecución y exponerlo. Aquí
se usa **Minikube**, un clúster de un solo nodo que corre en el computador local.

## Manifiestos

El `Deployment` declara que debe haber una réplica del contenedor `heart-api` escuchando en el
puerto 8000. Si el pod se cae, Kubernetes lo recrea.

```{literalinclude} /k8s/deployment.yaml
:language: yaml
:linenos:
```

El `Service` da una dirección estable a los pods con la etiqueta `app: heart-model` y redirige el
puerto 80 al 8000 del contenedor.

```{literalinclude} /k8s/service.yaml
:language: yaml
:linenos:
```

Respecto al ejemplo del enunciado, la imagen es `heart-api` (la construida localmente, sin
usuario de Docker Hub) y se añadió `imagePullPolicy: IfNotPresent` para que Kubernetes use esa
imagen local en lugar de intentar descargarla de internet.

## Despliegue

```bash
minikube start --driver=docker
minikube image load heart-api
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl get pods
kubectl get svc
minikube service heart-service
```

* `minikube image load` copia la imagen local dentro del clúster.
* En Minikube el `Service` de tipo `LoadBalancer` no recibe una IP externa (`EXTERNAL-IP` queda
  en `<pending>`); `minikube service` abre un túnel local hacia él.

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
