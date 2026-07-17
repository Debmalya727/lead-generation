from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Abstract base class for LLM provider adapters."""

    @abstractmethod
    async def complete(self, prompt: str, system_prompt: str = "") -> str:
        """
        Send a completion request to the LLM.

        Args:
            prompt: The user-facing prompt content.
            system_prompt: Optional system instructions for the model.

        Returns:
            The model's text response string.
        """
        raise NotImplementedError
