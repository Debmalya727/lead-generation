"""
Adapters for Phase 12.7A Enterprise AI Gateway.
Implements specific adapters for Gemini, OpenAI, Claude, Azure OpenAI,
Ollama, OpenRouter, Groq, Mistral, DeepSeek, and vLLM.
"""
import asyncio
import httpx
import logging
import json
import os
from typing import AsyncGenerator, Optional, Dict, Any
from app.ai.providers.base_llm import BaseLLMProvider
from app.ai.registry.provider_registry import ProviderRegistry
from app.config.settings import settings

logger = logging.getLogger("backend.ai.adapters")


class BaseAdapter(BaseLLMProvider):
    """Base class for all HTTP-based adapters."""

    def __init__(self, api_key: str = "", base_url: str = "", model: str = ""):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def _execute_with_retry(self, func, max_retries: int = 3, backoff: float = 0.5):
        last_err = None
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                last_err = e
                logger.warning(f"[{self.__class__.__name__}] Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff * (2 ** attempt))
        if last_err is not None:
            raise last_err
        raise RuntimeError("Operation failed after maximum retries.")

    async def complete_stream(self, prompt: str, system_prompt: str = "") -> AsyncGenerator[str, None]:
        """Default fallback stream yielding full completion chunk by chunk."""
        full_text = await self.complete(prompt, system_prompt)
        words = full_text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield chunk
            await asyncio.sleep(0.01)


class GeminiAdapter(BaseAdapter):
    """Adapter for Google Gemini API."""

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        api_key = self.api_key or os.getenv("GEMINI_API_KEY", "") or settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY")

        model_name = self.model or "gemini-1.5-flash"
        headers = {"Content-Type": "application/json"}

        if api_key.startswith("AQ.") or api_key.startswith("ya29."):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            headers["Authorization"] = f"Bearer {api_key}"
        else:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        async def _call():
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                try:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    return json.dumps(data)

        return await self._execute_with_retry(_call)


class OpenAIAdapter(BaseAdapter):
    """Adapter for OpenAI API."""

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        api_key = self.api_key or os.getenv("OPENAI_API_KEY", "") or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY")

        url = f"{self.base_url or 'https://api.openai.com/v1'}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model or "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.2
        }

        async def _call():
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]

        return await self._execute_with_retry(_call)


class ClaudeAdapter(BaseAdapter):
    """Adapter for Anthropic Claude API."""

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        api_key = self.api_key or os.getenv("CLAUDE_API_KEY", "") or os.getenv("ANTHROPIC_API_KEY", "") or settings.CLAUDE_API_KEY
        if not api_key:
            raise ValueError("Missing CLAUDE_API_KEY")

        url = f"{self.base_url or 'https://api.anthropic.com/v1'}/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": self.model or "claude-3-5-sonnet",
            "max_tokens": 4000,
            "messages": messages,
            "temperature": 0.2
        }
        if system_prompt:
            payload["system"] = system_prompt

        async def _call():
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["content"][0]["text"]

        return await self._execute_with_retry(_call)


class AzureOpenAIAdapter(BaseAdapter):
    """Adapter for Azure OpenAI Service."""

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        api_key = self.api_key or os.getenv("AZURE_OPENAI_API_KEY", "")
        endpoint = self.base_url or os.getenv("AZURE_OPENAI_ENDPOINT", "")
        if not api_key or not endpoint:
            raise ValueError("Missing Azure OpenAI configuration credentials")

        url = f"{endpoint.rstrip('/')}/chat/completions?api-version=2023-05-15"
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = {"messages": messages, "temperature": 0.2}

        async def _call():
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]

        return await self._execute_with_retry(_call)


class OllamaAdapter(BaseAdapter):
    """Adapter for local Ollama container or instance."""

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        url = f"{self.base_url or 'http://localhost:11434'}/api/chat"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model or "llama3",
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.2}
        }

        async def _call():
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["message"]["content"]

        return await self._execute_with_retry(_call)


class OpenRouterAdapter(BaseAdapter):
    """Adapter for OpenRouter API."""

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        api_key = self.api_key or os.getenv("OPENROUTER_API_KEY", "") or os.getenv("LLM_API_KEY", "") or settings.OPENROUTER_API_KEY
        if not api_key:
            raise ValueError("Missing OPENROUTER_API_KEY")

        url = f"{self.base_url or 'https://openrouter.ai/api/v1'}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://leadforge.ai",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model or "meta-llama/llama-3.1-8b-instruct",
            "messages": messages,
            "temperature": 0.2
        }

        async def _call():
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]

        return await self._execute_with_retry(_call)


class GroqAdapter(BaseAdapter):
    """Adapter for Groq API."""

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        api_key = self.api_key or os.getenv("GROQ_API_KEY", "") or settings.GROQ_API_KEY
        if not api_key:
            raise ValueError("Missing GROQ_API_KEY")

        url = f"{self.base_url or 'https://api.groq.com/openai/v1'}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model or "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.2
        }

        async def _call():
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]

        return await self._execute_with_retry(_call)


class MistralAdapter(BaseAdapter):
    """Adapter for Mistral AI API."""

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        api_key = self.api_key or os.getenv("MISTRAL_API_KEY", "") or settings.MISTRAL_API_KEY
        if not api_key:
            raise ValueError("Missing MISTRAL_API_KEY")

        url = f"{self.base_url or 'https://api.mistral.ai/v1'}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model or "mistral-small-latest",
            "messages": messages,
            "temperature": 0.2
        }

        async def _call():
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]

        return await self._execute_with_retry(_call)


class DeepSeekAdapter(BaseAdapter):
    """Adapter for DeepSeek API."""

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        api_key = self.api_key or os.getenv("DEEPSEEK_API_KEY", "") or settings.DEEPSEEK_API_KEY
        if not api_key:
            raise ValueError("Missing DEEPSEEK_API_KEY")

        url = f"{self.base_url or 'https://api.deepseek.com/v1'}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model or "deepseek-chat",
            "messages": messages,
            "temperature": 0.2
        }

        async def _call():
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]

        return await self._execute_with_retry(_call)


class VLLMAdapter(BaseAdapter):
    """Adapter for self-hosted vLLM instance."""

    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        url = f"{self.base_url or 'http://localhost:8000/v1'}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model or "default",
            "messages": messages,
            "temperature": 0.2
        }

        async def _call():
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
                return data["choices"][0]["message"]["content"]

        return await self._execute_with_retry(_call)


# Register all adapters dynamically into the ProviderRegistry
ProviderRegistry.register_provider("gemini", GeminiAdapter)
ProviderRegistry.register_provider("openai", OpenAIAdapter)
ProviderRegistry.register_provider("claude", ClaudeAdapter)
ProviderRegistry.register_provider("azure_openai", AzureOpenAIAdapter)
ProviderRegistry.register_provider("ollama", OllamaAdapter)
ProviderRegistry.register_provider("openrouter", OpenRouterAdapter)
ProviderRegistry.register_provider("groq", GroqAdapter)
ProviderRegistry.register_provider("mistral", MistralAdapter)
ProviderRegistry.register_provider("deepseek", DeepSeekAdapter)
ProviderRegistry.register_provider("vllm", VLLMAdapter)
