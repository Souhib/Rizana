from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    database_url: str
    jwt_secret_key: str
    jwt_encryption_algorithm: str
    resend_api_key: str
