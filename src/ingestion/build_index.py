import json

from langchain_community.vectorstores import FAISS

from src.config import get_settings
from src.embeddings import create_embeddings
from src.ingestion.load_data import load_knowledge_base, split_documents


def build_index() -> int:
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise RuntimeError(
            "Set OPENROUTER_API_KEY in your .env file. "
            "Get a free key at https://openrouter.ai/keys"
        )

    documents = load_knowledge_base(settings.knowledge_base_path)
    chunks = split_documents(documents)
    embeddings = create_embeddings(
        settings.openrouter_api_key,
        settings.openrouter_embedding_model,
    )
    vector_store = FAISS.from_documents(chunks, embeddings)
    settings.index_path.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(settings.index_path))

    with (settings.index_path / "documents.jsonl").open(
        "w", encoding="utf-8"
    ) as document_file:
        for chunk in chunks:
            document_file.write(
                json.dumps(
                    {"page_content": chunk.page_content, "metadata": chunk.metadata},
                    ensure_ascii=False,
                )
                + "\n"
            )

    return len(chunks)


if __name__ == "__main__":
    chunk_count = build_index()
    print(f"Saved {chunk_count} knowledge chunks to the FAISS index.")
