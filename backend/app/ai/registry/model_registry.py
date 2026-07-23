"""
Model Registry for Phase 12.7A Enterprise AI Gateway.
Details capacities, pricing, and capabilities of all models.
"""
from typing import Dict, Any, List, Optional


class ModelRegistry:
    """Registry tracking all models, context windows, capabilities, and pricing."""

    _models: Dict[str, Dict[str, Any]] = {
        # Gemini Models
        "gemini-1.5-flash": {
            "provider": "gemini",
            "name": "Gemini 1.5 Flash",
            "capabilities": ["vision", "tools", "structured", "streaming"],
            "context_window": 1048576,
            "input_token_price": 0.075,   # Price per 1M tokens
            "output_token_price": 0.30,   # Price per 1M tokens
            "is_embedding": False,
        },
        "gemini-1.5-pro": {
            "provider": "gemini",
            "name": "Gemini 1.5 Pro",
            "capabilities": ["vision", "tools", "structured", "streaming"],
            "context_window": 2097152,
            "input_token_price": 1.25,
            "output_token_price": 5.00,
            "is_embedding": False,
        },
        # OpenAI Models
        "gpt-4o-mini": {
            "provider": "openai",
            "name": "GPT-4o Mini",
            "capabilities": ["vision", "tools", "structured", "streaming"],
            "context_window": 128000,
            "input_token_price": 0.150,
            "output_token_price": 0.600,
            "is_embedding": False,
        },
        "gpt-4o": {
            "provider": "openai",
            "name": "GPT-4o",
            "capabilities": ["vision", "tools", "structured", "streaming"],
            "context_window": 128000,
            "input_token_price": 2.50,
            "output_token_price": 10.00,
            "is_embedding": False,
        },
        # Claude Models
        "claude-3-5-sonnet": {
            "provider": "claude",
            "name": "Claude 3.5 Sonnet",
            "capabilities": ["tools", "structured", "streaming"],
            "context_window": 200000,
            "input_token_price": 3.00,
            "output_token_price": 15.00,
            "is_embedding": False,
        },
        # DeepSeek Models
        "deepseek-chat": {
            "provider": "deepseek",
            "name": "DeepSeek V3",
            "capabilities": ["structured", "streaming"],
            "context_window": 64000,
            "input_token_price": 0.14,
            "output_token_price": 0.28,
            "is_embedding": False,
        },
        # OpenRouter default proxy model
        "openrouter-default": {
            "provider": "openrouter",
            "name": "OpenRouter Default",
            "capabilities": ["structured", "streaming"],
            "context_window": 128000,
            "input_token_price": 0.20,
            "output_token_price": 0.80,
            "is_embedding": False,
        },
        # Ollama local models
        "llama3": {
            "provider": "ollama",
            "name": "Llama 3 Local",
            "capabilities": ["structured", "streaming"],
            "context_window": 8192,
            "input_token_price": 0.0,
            "output_token_price": 0.0,
            "is_embedding": False,
        },
        # Embedding models
        "text-embedding-3-small": {
            "provider": "openai",
            "name": "Text Embedding 3 Small",
            "capabilities": [],
            "context_window": 8192,
            "input_token_price": 0.02,
            "output_token_price": 0.0,
            "is_embedding": True,
        },
        "text-embedding-004": {
            "provider": "gemini",
            "name": "Gemini text-embedding-004",
            "capabilities": [],
            "context_window": 2048,
            "input_token_price": 0.025,
            "output_token_price": 0.0,
            "is_embedding": True,
        },
        "all-minilm-l6-v2": {
            "provider": "ollama",
            "name": "SentenceTransformers Local",
            "capabilities": [],
            "context_window": 512,
            "input_token_price": 0.0,
            "output_token_price": 0.0,
            "is_embedding": True,
        },
    }

    @classmethod
    def get_model_info(cls, model_id: str) -> Optional[Dict[str, Any]]:
        """Fetch static model info."""
        return cls._models.get(model_id)

    @classmethod
    def list_models(cls) -> Dict[str, Dict[str, Any]]:
        """List all models."""
        return cls._models
