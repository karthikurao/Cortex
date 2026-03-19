"""Pytest bootstrap that isolates tests from machine-specific environment settings."""

import os

# Force a tool-independent provider for tests before application modules import settings.
os.environ["LLM_PROVIDER"] = "github"
os.environ["GITHUB_TOKEN"] = "test-token"
os.environ["MODEL_NAME"] = "gpt-4o"
os.environ["API_BASE_URL"] = "https://models.inference.ai.azure.com"

# Clear NVIDIA-specific values so tests never depend on local machine configuration.
os.environ.pop("NVIDIA_API_KEY", None)
