from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "LeadForgeAI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    MONGODB_URI: str = "mongodb://mongodb:27017"
    DATABASE_NAME: str = "leadforge"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    JWT_SECRET: str = "32-char-random-secret-key-placeholder"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()