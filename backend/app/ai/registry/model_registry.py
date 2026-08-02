"""
Centralized Model Registry for Phase 12.7 Enterprise AI Platform.
Stores context length, vision support, tool calling, streaming, pricing, speed score, quality score, and availability
across models for all 9 providers.
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("backend.ai.registry.model")


class ModelRegistry:
    """Centralized enterprise model registry."""

    _models: Dict[str, Dict[str, Any]] = {
        # 1. Gemini Models
        "gemini-1.5-flash": {
            "provider": "gemini",
            "name": "Gemini 1.5 Flash",
            "capabilities": ["vision", "tools", "structured", "streaming"],
            "context_length": 1048576,
            "context_window": 1048576,
            "vision_support": True,
            "tool_calling": True,
            "streaming": True,
            "input_token_price": 0.075,
            "output_token_price": 0.30,
            "speed_score": 9,
            "quality_score": 8,
            "availability": True,
            "is_embedding": False,
        },
        "gemini-1.5-pro": {
            "provider": "gemini",
            "name": "Gemini 1.5 Pro",
            "capabilities": ["vision", "tools", "structured", "streaming"],
            "context_length": 2097152,
            "context_window": 2097152,
            "vision_support": True,
            "tool_calling": True,
            "streaming": True,
            "input_token_price": 1.25,
            "output_token_price": 5.00,
            "speed_score": 7,
            "quality_score": 9.5,
            "availability": True,
            "is_embedding": False,
        },

        # 2. Groq Models
        "llama-3.3-70b-versatile": {
            "provider": "groq",
            "name": "Llama 3.3 70B Versatile (Groq)",
            "capabilities": ["tools", "structured", "streaming", "fast"],
            "context_length": 128000,
            "context_window": 128000,
            "vision_support": False,
            "tool_calling": True,
            "streaming": True,
            "input_token_price": 0.59,
            "output_token_price": 0.79,
            "speed_score": 10,
            "quality_score": 9,
            "availability": True,
            "is_embedding": False,
        },
        "mixtral-8x7b-32768": {
            "provider": "groq",
            "name": "Mixtral 8x7B (Groq)",
            "capabilities": ["structured", "streaming", "fast"],
            "context_length": 32768,
            "context_window": 32768,
            "vision_support": False,
            "tool_calling": True,
            "streaming": True,
            "input_token_price": 0.24,
            "output_token_price": 0.24,
            "speed_score": 10,
            "quality_score": 8,
            "availability": True,
            "is_embedding": False,
        },

        # 3. Mistral Models
        "mistral-small-latest": {
            "provider": "mistral",
            "name": "Mistral Small Latest",
            "capabilities": ["structured", "streaming"],
            "context_length": 32768,
            "context_window": 32768,
            "vision_support": False,
            "tool_calling": True,
            "streaming": True,
            "input_token_price": 0.20,
            "output_token_price": 0.60,
            "speed_score": 8.5,
            "quality_score": 8.2,
            "availability": True,
            "is_embedding": False,
        },
        "mistral-large-latest": {
            "provider": "mistral",
            "name": "Mistral Large Latest",
            "capabilities": ["tools", "structured", "streaming"],
            "context_length": 128000,
            "context_window": 128000,
            "vision_support": False,
            "tool_calling": True,
            "streaming": True,
            "input_token_price": 2.00,
            "output_token_price": 6.00,
            "speed_score": 7.5,
            "quality_score": 9.2,
            "availability": True,
            "is_embedding": False,
        },

        # 4. OpenRouter Models
        "meta-llama/llama-3.1-8b-instruct": {
            "provider": "openrouter",
            "name": "Llama 3.1 8B Instruct (OpenRouter)",
            "capabilities": ["structured", "streaming"],
            "context_length": 131072,
            "context_window": 131072,
            "vision_support": False,
            "tool_calling": True,
            "streaming": True,
            "input_token_price": 0.055,
            "output_token_price": 0.055,
            "speed_score": 9,
            "quality_score": 8.5,
            "availability": True,
            "is_embedding": False,
        },

        # 5. OpenAI Models
        "gpt-4o-mini": {
            "provider": "openai",
            "name": "GPT-4o Mini",
            "capabilities": ["vision", "tools", "structured", "streaming"],
            "context_length": 128000,
            "context_window": 128000,
            "vision_support": True,
            "tool_calling": True,
            "streaming": True,
            "input_token_price": 0.150,
            "output_token_price": 0.600,
            "speed_score": 9,
            "quality_score": 8.5,
            "availability": True,
            "is_embedding": False,
        },
        "gpt-4o": {
            "provider": "openai",
            "name": "GPT-4o Flagship",
            "capabilities": ["vision", "tools", "structured", "streaming"],
            "context_length": 128000,
            "context_window": 128000,
            "vision_support": True,
            "tool_calling": True,
            "streaming": True,
            "input_token_price": 2.50,
            "output_token_price": 10.00,
            "speed_score": 8,
            "quality_score": 9.8,
            "availability": True,
            "is_embedding": False,
        },

        # 6. Claude Models
        "claude-3-5-sonnet": {
            "provider": "claude",
            "name": "Claude 3.5 Sonnet",
            "capabilities": ["vision", "tools", "structured", "streaming"],
            "context_length": 200000,
            "context_window": 200000,
            "vision_support": True,
            "tool_calling": True,
            "streaming": True,
            "input_token_price": 3.00,
            "output_token_price": 15.00,
            "speed_score": 8,
            "quality_score": 9.9,
            "availability": True,
            "is_embedding": False,
        },

        # 7. DeepSeek Models
        "deepseek-chat": {
            "provider": "deepseek",
            "name": "DeepSeek V3 Chat",
            "capabilities": ["structured", "streaming", "reasoning"],
            "context_length": 64000,
            "context_window": 64000,
            "vision_support": False,
            "tool_calling": True,
            "streaming": True,
            "input_token_price": 0.14,
            "output_token_price": 0.28,
            "speed_score": 8.5,
            "quality_score": 9.4,
            "availability": True,
            "is_embedding": False,
        },

        # 8. Ollama Local Models
        "llama3": {
            "provider": "ollama",
            "name": "Llama 3 Local",
            "capabilities": ["structured", "streaming"],
            "context_length": 8192,
            "context_window": 8192,
            "vision_support": False,
            "tool_calling": False,
            "streaming": True,
            "input_token_price": 0.0,
            "output_token_price": 0.0,
            "speed_score": 7,
            "quality_score": 8,
            "availability": True,
            "is_embedding": False,
        },

        # 9. vLLM Local Models
        "vllm-default": {
            "provider": "vllm",
            "name": "vLLM Self-Hosted Engine",
            "capabilities": ["structured", "streaming", "fast"],
            "context_length": 32768,
            "context_window": 32768,
            "vision_support": False,
            "tool_calling": True,
            "streaming": True,
            "input_token_price": 0.0,
            "output_token_price": 0.0,
            "speed_score": 9.5,
            "quality_score": 8.5,
            "availability": True,
            "is_embedding": False,
        },

        # Embedding Models
        "text-embedding-3-small": {
            "provider": "openai",
            "name": "Text Embedding 3 Small",
            "capabilities": [],
            "context_length": 8192,
            "context_window": 8192,
            "vision_support": False,
            "tool_calling": False,
            "streaming": False,
            "input_token_price": 0.02,
            "output_token_price": 0.0,
            "speed_score": 9.5,
            "quality_score": 9.0,
            "availability": True,
            "is_embedding": True,
        },
    }

    @classmethod
    def register_model(cls, model_id: str, model_info: Dict[str, Any]) -> None:
        """Dynamically register or update a model specification."""
        cls._models[model_id] = model_info
        logger.info(f"Registered model '{model_id}' under provider '{model_info.get('provider')}'")

    @classmethod
    def get_model_info(cls, model_id: str) -> Optional[Dict[str, Any]]:
        """Fetch model metadata."""
        return cls._models.get(model_id)

    @classmethod
    def list_models(cls) -> Dict[str, Dict[str, Any]]:
        """List all registered models."""
        return cls._models

    @classmethod
    def get_models_by_provider(cls, provider: str) -> List[Dict[str, Any]]:
        """Retrieve models belonging to a given provider."""
        p = provider.lower().strip()
        return [{"model_id": k, **v} for k, v in cls._models.items() if v.get("provider") == p]
