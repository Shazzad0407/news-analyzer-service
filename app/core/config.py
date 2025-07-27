from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseSettings, Field


env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    REDIS_SERVER: str = Field("localhost", env="REDIS_SERVER")
    REDIS_PORT: str = Field(6379, env="REDIS_PORT")
    REDIS_PASSWORD: str = Field("redis_pass", env="REDIS_PASSWORD")
    REDIS_DATE_STAT_UPDATE_KEY: str = "DATE_KEY"
    REDIS_STATUS_UPDATE_KEY: str = "STATUS_KEY"

    MONGO_SERVER: str = Field("localhost", env="MONGO_SERVER")
    MONGO_PORT: str = Field("27017", env="MONGO_PORT")
    MONGO_USER: str = Field(..., env="MONGO_USER")
    MONGO_PASSWORD: str = Field(..., env="MONGO_PASSWORD")
    MONGO_DB: str = Field(..., env="MONGO_DB")
    MONGO_COLLECTION: str = Field(..., env="MONGO_COLLECTION")
    MONGO_URI: str = Field(..., env="MONGO_URI")

    CELERY_BROKER_URL: str = Field(..., env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(..., env="CELERY_RESULT_BACKEND")

    CHROMA_SERVER_AUTHN_PROVIDER: str = Field(..., env="CHROMA_SERVER_AUTHN_PROVIDER")
    CHROMA_SERVER_AUTHN_CREDENTIALS: str = Field(..., env="CHROMA_SERVER_AUTHN_CREDENTIALS")
    CHROMA_HOST: str = "news_chromadb"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION: str = "news_vector"

    # Polling intervals for the loops (in seconds)
    VECTORIZATION_POLL_INTERVAL: int = 10
    API_UPDATE_POLL_INTERVAL: int = 5

    BATCH_SIZE: int = 10

    # log info
    FILE_LOG_LEVEL: str = Field("DEBUG", env="FILE_LOG_LEVEL")

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
