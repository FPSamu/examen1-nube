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
            sns_secret = _get_secret("sales/sns", self.aws_region)
            self.sns_topic_arn = sns_secret["topic_arn"]

            s3_secret = _get_secret("sales/s3", self.aws_region)
            self.s3_bucket_name = s3_secret["bucket_name"]
        else:
            self.sns_topic_arn = os.environ["SNS_TOPIC_ARN"]
            self.s3_bucket_name = os.environ["S3_BUCKET_NAME"]


settings = Settings()
