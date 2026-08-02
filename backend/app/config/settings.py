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

    APIFY_API_TOKEN: str = ""

    # AI & Service API Keys
    GOOGLE_PLACES_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    RESEND_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    CLAUDE_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""

    def validate_api_keys(self) -> dict:
        """Validate configured API keys on application startup without crashing."""
        import logging
        logger = logging.getLogger("backend.config")
        
        status = {
            "GEMINI_API_KEY": bool(self.GEMINI_API_KEY),
            "GROQ_API_KEY": bool(self.GROQ_API_KEY),
            "MISTRAL_API_KEY": bool(self.MISTRAL_API_KEY),
            "OPENROUTER_API_KEY": bool(self.OPENROUTER_API_KEY),
            "RESEND_API_KEY": bool(self.RESEND_API_KEY),
            "OPENAI_API_KEY": bool(self.OPENAI_API_KEY),
            "CLAUDE_API_KEY": bool(self.CLAUDE_API_KEY),
            "DEEPSEEK_API_KEY": bool(self.DEEPSEEK_API_KEY),
        }
        
        configured = [k for k, v in status.items() if v]
        missing = [k for k, v in status.items() if not v]
        
        logger.info(f"🔑 [API Key Startup Validation] Configured keys ({len(configured)}): {', '.join(configured) if configured else 'None'}")
        if missing:
            logger.warning(f"⚠️ [API Key Startup Validation] Missing keys ({len(missing)}): {', '.join(missing)}")
        return status

    class Config:
        env_file = (".env", "backend/.env", "../backend/.env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()