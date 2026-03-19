"""Global configuration and settings for Cortex."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

# override=False (default) ensures system/user environment variables always take precedence
# over values in the .env file — critical so NVIDIA_API_KEY is never overridden by a blank .env entry.
load_dotenv(override=False)


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "github").lower())
    github_token: str = field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))
    nvidia_api_key: str = field(default_factory=lambda: os.getenv("NVIDIA_API_KEY", ""))
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "gpt-4o"))
    api_base_url: str = field(
        default_factory=lambda: os.getenv("API_BASE_URL", "https://models.inference.ai.azure.com")
    )
    ollama_base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "4096")))
    temperature: float = field(default_factory=lambda: float(os.getenv("TEMPERATURE", "0.3")))
    top_p: float = field(default_factory=lambda: float(os.getenv("TOP_P", "1.0")))
    verbose: bool = field(default_factory=lambda: os.getenv("VERBOSE", "false").lower() == "true")

    # Parallel execution settings
    parallel_execution: bool = field(default_factory=lambda: os.getenv("PARALLEL_EXECUTION", "true").lower() == "true")
    max_parallel_agents: int = field(default_factory=lambda: int(os.getenv("MAX_PARALLEL_AGENTS", "4")))
    max_delegation_depth: int = field(default_factory=lambda: int(os.getenv("MAX_DELEGATION_DEPTH", "3")))

    def validate(self) -> None:
        """Validate that required settings are configured."""
        if self.llm_provider == "nvidia" and not self.nvidia_api_key:
            raise ValueError(
                "NVIDIA_API_KEY is required when LLM_PROVIDER=nvidia. "
                "Set it in your .env file or as a system environment variable."
            )

        if self.llm_provider == "ollama":
            # Ollama runs locally — no API key required. Ensure a valid local model is set.
            if not self.model_name or self.model_name == "gpt-4o":
                self.model_name = "deepseek-r1"
            return

        if self.llm_provider != "nvidia" and not self.github_token:
            raise ValueError(
                "GITHUB_TOKEN is required. Set it in your .env file or as an environment variable. "
                "Get a token at: https://github.com/settings/tokens"
            )

    def get_llm_kwargs(self) -> dict:
        """Return kwargs for initializing the configured LangChain chat model."""
        if self.llm_provider == "nvidia":
            return {
                "model": self.model_name,
                "api_key": self.nvidia_api_key,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
            }

        if self.llm_provider == "ollama":
            return {
                "model": self.model_name,
                "base_url": self.ollama_base_url,
                "temperature": self.temperature,
            }

        return {
            "model": self.model_name,
            "api_key": self.github_token,
            "base_url": self.api_base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }


# Global singleton
settings = Settings()
