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
    debug: bool = False

    minio_root_user: SecretStr
    minio_root_password: SecretStr


app_settigns = AppSettings()
