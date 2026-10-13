from langchain_openai import OpenAIEmbeddings

OPENROUTER_EMBEDDING_BASE_URL = "https://openrouter.ai/api/v1"


def create_embeddings(
    api_key: str,
    model: str,
) -> OpenAIEmbeddings:
    """Return an embeddings client pointed at OpenRouter's OpenAI-compatible endpoint."""
    return OpenAIEmbeddings(
        model=model,
        base_url=OPENROUTER_EMBEDDING_BASE_URL,
        api_key=api_key,
    )
