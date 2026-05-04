#!/usr/bin/env bash
# =============================================================================
# infra/setup.sh – Provision all AWS resources for the Sales API on Kubernetes
# Prerequisites: AWS CLI configured, eksctl installed, kubectl installed
# Usage:
#   export NOTIFICATION_EMAIL="tu@correo.com"
#   export EXPEDIENTE="750900"          # default: 750900
#   bash infra/setup.sh
# =============================================================================
set -euo pipefail

# ---------- Configuration ----------------------------------------------------
AWS_REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
CLUSTER_NAME="sales-cluster"
DB_INSTANCE_ID="sales-db"
DB_NAME="salesdb"
DB_USER="salesadmin"
DB_PASSWORD="$(openssl rand -base64 20 | tr -dc 'A-Za-z0-9' | head -c 20)"
SQS_QUEUE_NAME="sales-sell-notes"
EXPEDIENTE="${EXPEDIENTE:-750900}"
S3_BUCKET_NAME="${EXPEDIENTE}-esi3898k-examen2"
SNS_TOPIC_NAME="sales-notifications"
NOTIFICATION_EMAIL="${NOTIFICATION_EMAIL:-your@email.com}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# -----------------------------------------------------------------------------

echo "Account ID : $ACCOUNT_ID"
echo "S3 Bucket  : $S3_BUCKET_NAME"
echo ""

# =============================================================================
echo "=== [1/7] Creating EKS cluster ==="
# Substitute real ACCOUNT_ID so eksctl can find the pre-existing LabRole.
CLUSTER_CONFIG="$(mktemp /tmp/cluster-XXXXXX.yaml)"
sed "s/ACCOUNT_ID_PLACEHOLDER/$ACCOUNT_ID/g" "$SCRIPT_DIR/cluster.yaml" > "$CLUSTER_CONFIG"
eksctl create cluster -f "$CLUSTER_CONFIG"
rm -f "$CLUSTER_CONFIG"

# Get the VPC created by eksctl so that RDS is in the same network as the pods.
EKS_VPC_ID=$(aws eks describe-cluster \
  --name "$CLUSTER_NAME" \
  --query "cluster.resourcesVpcConfig.vpcId" \
  --output text --region "$AWS_REGION")
echo "EKS VPC: $EKS_VPC_ID"

# =============================================================================
echo "=== [2/7] Creating SQS queue ==="
SQS_QUEUE_URL=$(aws sqs create-queue \
  --queue-name "$SQS_QUEUE_NAME" \
  --region "$AWS_REGION" \
  --query QueueUrl --output text)
echo "SQS URL: $SQS_QUEUE_URL"

# =============================================================================
echo "=== [3/7] Creating S3 bucket ==="
if [ "$AWS_REGION" = "us-east-1" ]; then
  aws s3api create-bucket --bucket "$S3_BUCKET_NAME" --region "$AWS_REGION"
else
  aws s3api create-bucket --bucket "$S3_BUCKET_NAME" --region "$AWS_REGION" \
    --create-bucket-configuration LocationConstraint="$AWS_REGION"
fi
echo "S3 Bucket: $S3_BUCKET_NAME"

# =============================================================================
echo "=== [4/7] Creating SNS topic and email subscription ==="
SNS_TOPIC_ARN=$(aws sns create-topic --name "$SNS_TOPIC_NAME" \
  --region "$AWS_REGION" --query TopicArn --output text)
aws sns subscribe \
  --topic-arn "$SNS_TOPIC_ARN" \
  --protocol email \
  --notification-endpoint "$NOTIFICATION_EMAIL" \
  --region "$AWS_REGION"
echo "SNS Topic ARN: $SNS_TOPIC_ARN"
echo ">>> Confirma la suscripción en tu email: $NOTIFICATION_EMAIL <<<"

# =============================================================================
echo "=== [5/7] Creating RDS PostgreSQL instance (inside EKS VPC) ==="

# Use EKS subnets so pods can reach the database without cross-VPC routing.
SUBNET_IDS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$EKS_VPC_ID" \
  --query "Subnets[*].SubnetId" --output text --region "$AWS_REGION" | tr '\t' ',')

SG_ID=$(aws ec2 create-security-group \
  --group-name "sales-rds-sg" \
  --description "Allow PostgreSQL from EKS nodes" \
  --vpc-id "$EKS_VPC_ID" \
  --region "$AWS_REGION" \
  --query GroupId --output text)
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --protocol tcp --port 5432 --cidr "0.0.0.0/0" \
  --region "$AWS_REGION"

aws rds create-db-subnet-group \
  --db-subnet-group-name "sales-db-subnet-group" \
  --db-subnet-group-description "Sales DB subnet group" \
  --subnet-ids $(echo "$SUBNET_IDS" | tr ',' ' ') \
  --region "$AWS_REGION" || true

aws rds create-db-instance \
  --db-instance-identifier "$DB_INSTANCE_ID" \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version "16" \
  --master-username "$DB_USER" \
  --master-user-password "$DB_PASSWORD" \
  --db-name "$DB_NAME" \
  --allocated-storage 20 \
  --db-subnet-group-name "sales-db-subnet-group" \
  --vpc-security-group-ids "$SG_ID" \
  --no-publicly-accessible \
  --region "$AWS_REGION"

echo "Waiting for RDS instance (~5 min)..."
aws rds wait db-instance-available \
  --db-instance-identifier "$DB_INSTANCE_ID" \
  --region "$AWS_REGION"

DB_HOST=$(aws rds describe-db-instances \
  --db-instance-identifier "$DB_INSTANCE_ID" \
  --query "DBInstances[0].Endpoint.Address" \
  --output text --region "$AWS_REGION")
echo "RDS endpoint: $DB_HOST"

# =============================================================================
echo "=== [6/7] Storing secrets in Secrets Manager ==="
aws secretsmanager create-secret \
  --name "sales/db" --region "$AWS_REGION" \
  --secret-string "{\"host\":\"$DB_HOST\",\"port\":\"5432\",\"name\":\"$DB_NAME\",\"user\":\"$DB_USER\",\"password\":\"$DB_PASSWORD\"}"

aws secretsmanager create-secret \
  --name "sales/sqs" --region "$AWS_REGION" \
  --secret-string "{\"queue_url\":\"$SQS_QUEUE_URL\"}"

aws secretsmanager create-secret \
  --name "sales/s3" --region "$AWS_REGION" \
  --secret-string "{\"bucket_name\":\"$S3_BUCKET_NAME\"}"

aws secretsmanager create-secret \
  --name "sales/sns" --region "$AWS_REGION" \
  --secret-string "{\"topic_arn\":\"$SNS_TOPIC_ARN\"}"

# =============================================================================
echo "=== [7/7] Applying Kubernetes manifests ==="
K8S_DIR="$SCRIPT_DIR/../k8s"
kubectl apply -f "$K8S_DIR/configmap.yaml"
kubectl apply -f "$K8S_DIR/api-deployment.yaml"
kubectl apply -f "$K8S_DIR/api-service.yaml"
kubectl apply -f "$K8S_DIR/receipt-worker-deployment.yaml"
kubectl apply -f "$K8S_DIR/pdf-generator-deployment.yaml"
kubectl apply -f "$K8S_DIR/pdf-generator-service.yaml"
kubectl apply -f "$K8S_DIR/notifier-deployment.yaml"
kubectl apply -f "$K8S_DIR/notifier-service.yaml"

echo ""
echo "============================================================"
echo "Infraestructura aprovisionada exitosamente."
echo ""
echo "  DB_HOST   : $DB_HOST"
echo "  DB_USER   : $DB_USER"
echo "  DB_PASS   : $DB_PASSWORD"
echo "  SQS URL   : $SQS_QUEUE_URL"
echo "  S3 Bucket : $S3_BUCKET_NAME"
echo "  SNS ARN   : $SNS_TOPIC_ARN"
echo ""
echo "Siguientes pasos:"
echo "  1. Confirmar suscripción SNS en el email."
echo "  2. Correr el schema SQL (ver abajo)."
echo "  3. Obtener URL del LoadBalancer:"
echo "       kubectl get svc api-service"
echo "  4. Actualizar API_BASE_URL en k8s/configmap.yaml y aplicar:"
echo "       kubectl apply -f k8s/configmap.yaml"
echo "       kubectl rollout restart deployment/api deployment/receipt-worker"
echo ""
echo "--- Schema migration (ejecutar desde WSL): ---"
echo "kubectl run psql-migration --image=postgres:15 --restart=Never -it --rm \\"
echo "  --env=PGPASSWORD=$DB_PASSWORD -- \\"
echo "  psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f /dev/stdin"
echo "============================================================"
