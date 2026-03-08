from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str

    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # S3
    s3_bucket_name: str = "750900-esi3898k-examen1"

    # SNS
    sns_topic_arn: str

    # API
    api_base_url: str = "http://localhost:8000"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
