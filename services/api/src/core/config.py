import json
import os

import boto3


def _get_secret(secret_name: str, region: str) -> dict:
    client = boto3.client("secretsmanager", region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])


class Settings:
    def __init__(self):
        self.aws_region = os.environ.get("AWS_REGION", "us-east-1")
        use_sm = os.environ.get("USE_SECRETS_MANAGER", "false").lower() == "true"

        if use_sm:
            db_secret = _get_secret("sales/db", self.aws_region)
            self.db_host = db_secret["host"]
            self.db_port = int(db_secret.get("port", 5432))
            self.db_name = db_secret["name"]
            self.db_user = db_secret["user"]
            self.db_password = db_secret["password"]

            sqs_secret = _get_secret("sales/sqs", self.aws_region)
            self.sqs_queue_url = sqs_secret["queue_url"]

            s3_secret = _get_secret("sales/s3", self.aws_region)
            self.s3_bucket_name = s3_secret["bucket_name"]
        else:
            self.db_host = os.environ["DB_HOST"]
            self.db_port = int(os.environ.get("DB_PORT", "5432"))
            self.db_name = os.environ["DB_NAME"]
            self.db_user = os.environ["DB_USER"]
            self.db_password = os.environ["DB_PASSWORD"]
            self.sqs_queue_url = os.environ["SQS_QUEUE_URL"]
            self.s3_bucket_name = os.environ.get("S3_BUCKET_NAME", "")

        # Non-sensitive inter-service URLs (injected via ConfigMap)
        self.api_base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
        self.notifier_url = os.environ.get("NOTIFIER_URL", "http://notifier-service:8003")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?sslmode=require"
        )


settings = Settings()
