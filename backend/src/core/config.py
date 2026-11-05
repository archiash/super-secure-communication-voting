from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"

class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    ibm_token: str = ""
    use_ibm_quantum: bool = False
    use_real_ibm_hardware: bool = False

    model_config = SettingsConfigDict(
        env_file=(_ENV_FILE if _ENV_FILE.exists() else ".env"),
        extra="ignore"
    )

settings = Settings()
