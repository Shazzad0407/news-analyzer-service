import secrets
from pathlib import Path
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from pydantic import BaseSettings, PostgresDsn, validator, Field, EmailStr


env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    # project general info
    PROJECT_TITLE: str = "News Analyzer Service"
    PROJECT_DESCRIPTION: str = "The backend APIs for News Analyzer Service."
    PROJECT_VERSION: str = "0.0.1"

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 5203

    API_V1_STR: str = "/api/v1"
    ALLOWED_HOST: str = "*"
    ALLOWED_METHOD: str = "*"
    ALLOWED_HEADERS: str = "*"
    ORIGINS: List = ["*"]

    MONGO_SERVER: str = Field("localhost", env="MONGO_SERVER")
    MONGO_PORT: str = Field("27017", env="MONGO_PORT")
    MONGO_USER: str = Field(..., env="MONGO_USER")
    MONGO_PASSWORD: str = Field(..., env="MONGO_PASSWORD")
    MONGO_DB: str = Field(..., env="MONGO_DB")


    # log info
    FILE_LOG_LEVEL: str = Field("DEBUG", env="FILE_LOG_LEVEL")

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
