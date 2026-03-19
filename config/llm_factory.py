"""Factory helpers for constructing LLM chat clients based on settings."""

from typing import Any

from langchain_openai import ChatOpenAI

try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
except ImportError:
    ChatNVIDIA = None

try:
    from langchain_ollama import ChatOllama
except ImportError:
    ChatOllama = None

from config.settings import Settings


def create_chat_model(settings: Settings) -> Any:
    """Return a configured LangChain chat model for the active provider."""
    if settings.llm_provider == "nvidia":
        if ChatNVIDIA is None:
            raise ImportError(
                "langchain-nvidia-ai-endpoints is required for LLM_PROVIDER=nvidia. "
                "Install it with: pip install langchain-nvidia-ai-endpoints"
            )
        return ChatNVIDIA(**settings.get_llm_kwargs())

    if settings.llm_provider == "ollama":
        if ChatOllama is None:
            raise ImportError(
                "langchain-ollama is required for LLM_PROVIDER=ollama. Install it with: pip install langchain-ollama"
            )
        return ChatOllama(**settings.get_llm_kwargs())

    return ChatOpenAI(**settings.get_llm_kwargs())
