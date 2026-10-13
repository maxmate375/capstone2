from src.config import get_settings


def test_settings_read_openrouter_configuration(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key")
    monkeypatch.setenv("OPENROUTER_CHAT_MODEL", "openai/gpt-4o-mini")
    monkeypatch.setenv("OPENROUTER_EMBEDDING_MODEL", "openai/text-embedding-3-large")

    settings = get_settings()

    assert settings.openrouter_api_key == "sk-or-v1-test-key"
    assert settings.openrouter_chat_model == "openai/gpt-4o-mini"
    assert settings.openrouter_embedding_model == "openai/text-embedding-3-large"


def test_settings_use_openrouter_defaults(monkeypatch):
    for variable in (
        "OPENROUTER_API_KEY",
        "OPENROUTER_CHAT_MODEL",
        "OPENROUTER_EMBEDDING_MODEL",
    ):
        monkeypatch.delenv(variable, raising=False)

    settings = get_settings()

    assert settings.openrouter_api_key is None
    assert settings.openrouter_chat_model == "google/gemini-2.0-flash-001"
    assert settings.openrouter_embedding_model == "openai/text-embedding-3-small"
