#!/usr/bin/env bash
# =============================================================================
# infra/setup.sh – Provision all AWS resources for the sales API on Kubernetes
# Prerequisites: AWS CLI configured, eksctl installed, kubectl installed
# Usage: bash infra/setup.sh
# =============================================================================
set -euo pipefail

# ---------- Configuration (edit these) ---------------------------------------
AWS_REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
CLUSTER_NAME="sales-cluster"
DB_INSTANCE_ID="sales-db"
DB_NAME="salesdb"
DB_USER="salesadmin"
DB_PASSWORD="$(openssl rand -base64 20 | tr -dc 'A-Za-z0-9' | head -c 20)"
SQS_QUEUE_NAME="sales-sell-notes"
EXPEDIENTE="${EXPEDIENTE:-750900}"           # set via env: export EXPEDIENTE=xxxxxx
S3_BUCKET_NAME="${EXPEDIENTE}-esi3898k-examen2"
SNS_TOPIC_NAME="sales-notifications"
NOTIFICATION_EMAIL="${NOTIFICATION_EMAIL:-your@email.com}"  # override via env
# -----------------------------------------------------------------------------

echo "=== [1/8] Creating EKS cluster ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
eksctl create cluster -f "$SCRIPT_DIR/cluster.yaml"

echo "=== [2/8] Creating SQS queue ==="
SQS_QUEUE_URL=$(aws sqs create-queue \
  --queue-name "$SQS_QUEUE_NAME" \
  --region "$AWS_REGION" \
  --query QueueUrl --output text)
echo "SQS Queue URL: $SQS_QUEUE_URL"

echo "=== [3/8] Creating S3 bucket ==="
if [ "$AWS_REGION" = "us-east-1" ]; then
  aws s3api create-bucket --bucket "$S3_BUCKET_NAME" --region "$AWS_REGION"
else
  aws s3api create-bucket --bucket "$S3_BUCKET_NAME" --region "$AWS_REGION" \
    --create-bucket-configuration LocationConstraint="$AWS_REGION"
fi
echo "S3 Bucket: $S3_BUCKET_NAME"

echo "=== [4/8] Creating SNS topic and email subscription ==="
SNS_TOPIC_ARN=$(aws sns create-topic --name "$SNS_TOPIC_NAME" \
  --region "$AWS_REGION" --query TopicArn --output text)
aws sns subscribe \
  --topic-arn "$SNS_TOPIC_ARN" \
  --protocol email \
  --notification-endpoint "$NOTIFICATION_EMAIL" \
  --region "$AWS_REGION"
echo "SNS Topic ARN: $SNS_TOPIC_ARN"
echo "Confirm the subscription in your email: $NOTIFICATION_EMAIL"

echo "=== [5/8] Creating RDS PostgreSQL instance ==="
# Get default VPC and subnets
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" \
  --query "Vpcs[0].VpcId" --output text --region "$AWS_REGION")
SUBNET_IDS=$(aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query "Subnets[*].SubnetId" --output text --region "$AWS_REGION" | tr '\t' ',')

# Security group: allow PostgreSQL from anywhere within VPC
SG_ID=$(aws ec2 create-security-group \
  --group-name "sales-rds-sg" \
  --description "Allow PostgreSQL from EKS nodes" \
  --vpc-id "$VPC_ID" \
  --region "$AWS_REGION" \
  --query GroupId --output text)
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --protocol tcp --port 5432 --cidr "0.0.0.0/0" \
  --region "$AWS_REGION"

# DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name "sales-db-subnet-group" \
  --db-subnet-group-description "Sales DB subnet group" \
  --subnet-ids $(echo "$SUBNET_IDS" | tr ',' ' ') \
  --region "$AWS_REGION" || true

aws rds create-db-instance \
  --db-instance-identifier "$DB_INSTANCE_ID" \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version "15.4" \
  --master-username "$DB_USER" \
  --master-user-password "$DB_PASSWORD" \
  --db-name "$DB_NAME" \
  --allocated-storage 20 \
  --db-subnet-group-name "sales-db-subnet-group" \
  --vpc-security-group-ids "$SG_ID" \
  --no-publicly-accessible \
  --region "$AWS_REGION"

echo "Waiting for RDS instance to be available (this may take ~5 minutes)..."
aws rds wait db-instance-available \
  --db-instance-identifier "$DB_INSTANCE_ID" \
  --region "$AWS_REGION"

DB_HOST=$(aws rds describe-db-instances \
  --db-instance-identifier "$DB_INSTANCE_ID" \
  --query "DBInstances[0].Endpoint.Address" \
  --output text --region "$AWS_REGION")
echo "RDS endpoint: $DB_HOST"

echo "=== [6/8] Storing secrets in Secrets Manager ==="
aws secretsmanager create-secret \
  --name "sales/db" \
  --region "$AWS_REGION" \
  --secret-string "{\"host\":\"$DB_HOST\",\"port\":\"5432\",\"name\":\"$DB_NAME\",\"user\":\"$DB_USER\",\"password\":\"$DB_PASSWORD\"}"

aws secretsmanager create-secret \
  --name "sales/sqs" \
  --region "$AWS_REGION" \
  --secret-string "{\"queue_url\":\"$SQS_QUEUE_URL\"}"

aws secretsmanager create-secret \
  --name "sales/s3" \
  --region "$AWS_REGION" \
  --secret-string "{\"bucket_name\":\"$S3_BUCKET_NAME\"}"

aws secretsmanager create-secret \
  --name "sales/sns" \
  --region "$AWS_REGION" \
  --secret-string "{\"topic_arn\":\"$SNS_TOPIC_ARN\"}"

echo "=== [7/8] Attaching LabRole to node group (IAM access for pods) ==="
NODE_GROUP_ROLE=$(aws eks describe-nodegroup \
  --cluster-name "$CLUSTER_NAME" \
  --nodegroup-name standard-workers \
  --region "$AWS_REGION" \
  --query "nodegroup.nodeRole" --output text | awk -F/ '{print $NF}')

for policy in \
  "arn:aws:iam::aws:policy/AmazonSQSFullAccess" \
  "arn:aws:iam::aws:policy/AmazonS3FullAccess" \
  "arn:aws:iam::aws:policy/AmazonSNSFullAccess" \
  "arn:aws:iam::aws:policy/SecretsManagerReadWrite"; do
  aws iam attach-role-policy \
    --role-name "$NODE_GROUP_ROLE" \
    --policy-arn "$policy" || true
done

echo "=== [8/8] Applying Kubernetes manifests ==="
kubectl apply -f ../k8s/configmap.yaml
kubectl apply -f ../k8s/api-deployment.yaml
kubectl apply -f ../k8s/api-service.yaml
kubectl apply -f ../k8s/receipt-worker-deployment.yaml
kubectl apply -f ../k8s/pdf-generator-deployment.yaml
kubectl apply -f ../k8s/pdf-generator-service.yaml
kubectl apply -f ../k8s/notifier-deployment.yaml
kubectl apply -f ../k8s/notifier-service.yaml

echo ""
echo "=========================================="
echo "Infrastructure provisioned successfully."
echo "DB host:       $DB_HOST"
echo "SQS URL:       $SQS_QUEUE_URL"
echo "S3 Bucket:     $S3_BUCKET_NAME"
echo "SNS Topic ARN: $SNS_TOPIC_ARN"
echo ""
echo "Next steps:"
echo "  1. Confirm the SNS subscription email."
echo "  2. Update k8s/configmap.yaml with the API LoadBalancer URL once assigned."
echo "  3. Run the DB schema migration (see README.md)."
echo "=========================================="
