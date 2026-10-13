from src.embeddings import OPENROUTER_EMBEDDING_BASE_URL, create_embeddings


def test_create_embeddings_uses_openrouter_endpoint(monkeypatch):
    captured = {}

    def fake_openai_embeddings(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(
        "src.embeddings.OpenAIEmbeddings", fake_openai_embeddings
    )

    result = create_embeddings(
        api_key="sk-or-v1-test-key",
        model="openai/text-embedding-3-small",
    )

    assert result is not None
    assert captured == {
        "model": "openai/text-embedding-3-small",
        "base_url": OPENROUTER_EMBEDDING_BASE_URL,
        "api_key": "sk-or-v1-test-key",
    }
