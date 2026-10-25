from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class VseGPTSettings(BaseSettings):
    api_token: SecretStr
    url: str
    model: str
    max_connections: int | None = Field(default=None, gt=0)


class UnsplashSettings(BaseSettings):
    api_token: SecretStr
    max_connections: int | None = Field(gt=0)
    timeout: int | None = Field(gt=0)


class S3Settings(BaseSettings):
    endpoint_url: str
    access_key: SecretStr
    secret_key: SecretStr
    bucket_name: str
    connect_timeout: int | None = Field(default=10, gt=0)
    read_timeout: int | None = Field(default=10, gt=0)
    max_connections: int | None = Field(default=10, gt=0)


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        validate_default=True,
        env_nested_delimiter='__',
    )

    vsegpt: VseGPTSettings
    unsplash: UnsplashSettings
    s3: S3Settings
    debug: bool = False


app_settigns = AppSettings()
