import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CivicOS_WestBengal"
    API_V1_STR: str = "/api/v1"
    
    # Database configuration matching docker-compose
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "civic_admin")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "secret_password")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "civic_os_dev")
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()