"""Tests for LLM configuration resolution."""

from app.core.config import Settings


def test_resolved_llm_base_url_prefers_llm_base_url() -> None:
    """LLM_BASE_URL should override OPENAI_BASE_URL when both are provided."""
    settings = Settings(
        openai_api_key="openai-key",
        openai_base_url="https://openai.example.com/v1",
        llm_api_key="llm-key",
        llm_base_url="https://llm.example.com/v1",
        _env_file=None,
    )

    assert settings.resolved_llm_base_url == "https://llm.example.com/v1"


def test_resolved_llm_base_url_falls_back_to_openai_base_url() -> None:
    """OPENAI_BASE_URL should be used when provider-agnostic LLM_BASE_URL is absent."""
    settings = Settings(
        openai_api_key="openai-key",
        openai_base_url="https://openai.example.com/v1",
        llm_api_key="",
        llm_base_url="",
        _env_file=None,
    )

    assert settings.resolved_llm_base_url == "https://openai.example.com/v1"


def test_resolved_llm_api_key_falls_back_to_openai_api_key() -> None:
    """OPENAI_API_KEY should be used when LLM_API_KEY is not set."""
    settings = Settings(
        openai_api_key="openai-key",
        llm_api_key="",
        _env_file=None,
    )

    assert settings.resolved_llm_api_key == "openai-key"
