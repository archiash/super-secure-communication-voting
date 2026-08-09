from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    qkd_api_url: str
    mongodb_uri: str
    ibm_token: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()