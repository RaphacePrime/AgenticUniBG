# Configurazione
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Impostazioni dell'applicazione
    """
    # API Keys
    # groq_api_key: str
    google_api_key: str
    tavily_api_key: str
    
    # App settings
    environment: str = "development"
    debug: bool = True
    
    # CORS
    cors_origins: list = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
