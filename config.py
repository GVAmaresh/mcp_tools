import os
from pydantic_settings import BaseSettings
from pydantic import RedisDsn

class Settings(BaseSettings):
    APP_ENV: str = "development"
    LOG_LEVEL: str = "DEBUG"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_USER: str = "default" 
    REDIS_PASSWORD: str | None = None
    REDIS_DB: int = 0
    REDIS_URL: RedisDsn = "redis://redis:6379/0" 

    SERPAPI_API_KEY: str = "your_serpapi_api_key_here"
    GOOGLE_MAPS_API_KEY: str= "your_google_maps_api_key_here"

    # @property
    # def redis_url(self) -> str:
    #     if self.REDIS_PASSWORD:
    #         return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    #     return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()