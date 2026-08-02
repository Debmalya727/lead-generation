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

    # LLM Providers Configuration
    OPENROUTER_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_API_KEY: str = ""
    HUGGINGFACE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Multi-Agent Model Architecture Routing
    MANAGER_AGENT_PROVIDER: str = "openrouter"
    MANAGER_AGENT_MODEL: str = "nvidia/nemotron-3-ultra"

    PLANNER_AGENT_PROVIDER: str = "groq"
    PLANNER_AGENT_MODEL: str = "gpt-oss-20b"

    SCRAPER_AGENT_PROVIDER: str = "ollama"
    SCRAPER_AGENT_MODEL: str = "qwen3:4b"

    RESEARCH_AGENT_PROVIDER: str = "groq"
    RESEARCH_AGENT_MODEL: str = "llama-3.3-70b"

    WEBSITE_ANALYZER_PROVIDER: str = "ollama"
    WEBSITE_ANALYZER_MODEL: str = "gemma3:12b"

    FALLBACK_PROVIDER: str = "openrouter"
    FALLBACK_MODEL: str = "openrouter/free"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()