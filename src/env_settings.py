from pydantic import AnyHttpUrl, PositiveInt, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class VseGPTSettings(BaseSettings):
    api_token: SecretStr
    url: AnyHttpUrl
    model: str
    max_connections: PositiveInt | None = 5


class UnsplashSettings(BaseSettings):
    api_token: SecretStr
    max_connections: PositiveInt | None
    timeout: PositiveInt | None


class S3Settings(BaseSettings):
    endpoint_url: AnyHttpUrl
    access_key: SecretStr
    secret_key: SecretStr
    bucket_name: str
    connect_timeout: PositiveInt | None = 10
    read_timeout: PositiveInt | None = 10
    max_connections: PositiveInt | None = 10


class GotenbergSettings(BaseSettings):
    api_url: AnyHttpUrl = AnyHttpUrl('https://demo.gotenberg.dev')
    width: PositiveInt = 1000
    format: str = 'png'
    max_connections: PositiveInt = 5
    timeout: PositiveInt = 15
    wait_delay: PositiveInt = 8


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
    gotenberg: GotenbergSettings
    debug: bool = False


app_settigns = AppSettings()
