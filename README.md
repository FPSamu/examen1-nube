# Sales API – Kubernetes Edition

REST API de ventas desplegada como microservicios en Kubernetes (EKS).

## Estructura del repositorio

```
services/
  api/              # CRUD de clientes, domicilios, productos, notas de venta
  receipt-worker/   # Consumidor SQS – coordina generación de PDF y notificación
  pdf-generator/    # Genera PDF, lo sube a S3, devuelve la S3 key
  notifier/         # Envía correo via SNS, actualiza metadatos en S3
k8s/                # Manifiestos de Kubernetes
infra/              # Scripts de infraestructura AWS
```

## Pods y Services

| Pod             | Service       | Tipo         | Razón |
|-----------------|---------------|--------------|-------|
| api             | api-service   | LoadBalancer | Único pod con tráfico externo |
| pdf-generator   | pdf-generator-service | ClusterIP | Solo llamado internamente por receipt-worker |
| notifier        | notifier-service | ClusterIP | Solo llamado internamente por receipt-worker y api |
| receipt-worker  | —             | Ninguno      | Consume SQS (pull), nunca recibe tráfico entrante |

## Secretos

Todos los valores sensibles se almacenan en **AWS Secrets Manager** bajo las claves:

- `sales/db` – credenciales RDS
- `sales/sqs` – URL de la cola SQS
- `sales/s3` – nombre del bucket S3
- `sales/sns` – ARN del topic SNS

Los pods los leen en tiempo de ejecución mediante boto3. La variable `USE_SECRETS_MANAGER=true` activa este modo. Los nodos del clúster tienen el LabRole/node-role con las políticas necesarias.

## Despliegue completo

### Requisitos previos
- AWS CLI configurado con credenciales válidas
- `eksctl` instalado
- `kubectl` instalado

### 1. Provisionar infraestructura

```bash
export NOTIFICATION_EMAIL="correo@ejemplo.com"
export EXPEDIENTE="750900"
bash infra/setup.sh
```

El script usa `infra/cluster.yaml` para crear el clúster EKS con `eksctl`, luego provisiona RDS, SQS, S3 (`{EXPEDIENTE}-esi3898k-examen2`), SNS y Secrets Manager, y aplica los manifiestos de Kubernetes.

Para crear solo el clúster manualmente:

```bash
eksctl create cluster -f infra/cluster.yaml
```

### 2. Schema de la base de datos

Conéctate a la instancia RDS y ejecuta:

```sql
CREATE TYPE tipo_direccion_enum AS ENUM ('FACTURACIÓN', 'ENVÍO');

CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    razon_social VARCHAR(255) NOT NULL,
    nombre_comercial VARCHAR(255) NOT NULL,
    rfc VARCHAR(13) NOT NULL UNIQUE,
    correo_electronico VARCHAR(255) NOT NULL,
    telefono VARCHAR(20) NOT NULL
);

CREATE TABLE addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    domicilio VARCHAR(255) NOT NULL,
    colonia VARCHAR(255) NOT NULL,
    municipio VARCHAR(255) NOT NULL,
    estado VARCHAR(255) NOT NULL,
    tipo_direccion tipo_direccion_enum NOT NULL
);

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre VARCHAR(255) NOT NULL,
    unidad_medida VARCHAR(50) NOT NULL,
    precio_base NUMERIC(12,2) NOT NULL
);

CREATE TABLE sell_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    folio VARCHAR(50) NOT NULL UNIQUE,
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE RESTRICT,
    direccion_facturacion_id UUID NOT NULL REFERENCES addresses(id) ON DELETE RESTRICT,
    direccion_envio_id UUID NOT NULL REFERENCES addresses(id) ON DELETE RESTRICT,
    total NUMERIC(12,2) NOT NULL,
    pdf_s3_key VARCHAR(512)
);

CREATE TABLE sell_note_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sell_note_id UUID NOT NULL REFERENCES sell_notes(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    cantidad NUMERIC(10,3) NOT NULL,
    precio_unitario NUMERIC(12,2) NOT NULL,
    importe NUMERIC(12,2) NOT NULL
);
```

### 3. Construir y publicar imágenes Docker

```bash
DOCKERHUB_USER="samupif"

# api
docker build -t $DOCKERHUB_USER/sales-api:latest services/api/
docker push $DOCKERHUB_USER/sales-api:latest

# receipt-worker
docker build -t $DOCKERHUB_USER/sales-receipt-worker:latest services/receipt-worker/
docker push $DOCKERHUB_USER/sales-receipt-worker:latest

# pdf-generator
docker build -t $DOCKERHUB_USER/sales-pdf-generator:latest services/pdf-generator/
docker push $DOCKERHUB_USER/sales-pdf-generator:latest

# notifier
docker build -t $DOCKERHUB_USER/sales-notifier:latest services/notifier/
docker push $DOCKERHUB_USER/sales-notifier:latest
```

Los YAMLs ya tienen configurado el usuario `samupif`.

### 4. Actualizar ConfigMap con URL externa

Una vez que el LoadBalancer tenga dirección:

```bash
kubectl get svc api-service
```

Edita `k8s/configmap.yaml`, actualiza `API_BASE_URL` con la dirección del LoadBalancer y aplica:

```bash
kubectl apply -f k8s/configmap.yaml
kubectl rollout restart deployment/api
kubectl rollout restart deployment/receipt-worker
```

## Flujo de creación de nota de venta

```
Cliente → POST /api/v1/sell-notes
    → api valida, persiste en RDS, publica sell_note_id en SQS → responde 201

receipt-worker (SQS long-poll)
    → lee sell_note_id
    → consulta RDS para obtener datos completos
    → POST http://pdf-generator-service:8001/generate  → recibe s3_key
    → actualiza pdf_s3_key en RDS
    → POST http://notifier-service:8003/notify  → SNS envía email
    → elimina mensaje de SQS
```

## Variables de entorno locales (desarrollo)

Copia `.env.example` a `.env` y llena los valores. Con `USE_SECRETS_MANAGER=false` los servicios leen de variables de entorno en lugar de Secrets Manager.
