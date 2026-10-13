import json
from pathlib import Path
from threading import Lock

from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from src.embeddings import create_embeddings


class HybridRetriever:
    def __init__(
        self,
        vector_store: FAISS,
        documents: list[Document],
        semantic_weight: float = 0.65,
    ) -> None:
        if not documents:
            raise ValueError("The hybrid retriever requires at least one document.")
        if not 0 <= semantic_weight <= 1:
            raise ValueError("semantic_weight must be between 0 and 1.")
        self.vector_store = vector_store
        self.documents = documents
        self.semantic_weight = semantic_weight
        self.keyword_retriever = BM25Retriever.from_documents(documents)
        self._keyword_search_lock = Lock()

    def search(self, query: str, k: int = 4) -> list[tuple[Document, float]]:
        if not query.strip():
            raise ValueError("Search query cannot be empty.")
        if k < 1:
            raise ValueError("k must be at least 1.")

        candidate_k = k * 4
        semantic_docs = self.vector_store.similarity_search(query, k=candidate_k)
        with self._keyword_search_lock:
            self.keyword_retriever.k = candidate_k
            keyword_docs = self.keyword_retriever.invoke(query)

        ranked: dict[str, tuple[Document, float]] = {}
        for weight, results in (
            (self.semantic_weight, semantic_docs),
            (1 - self.semantic_weight, keyword_docs),
        ):
            for rank, document in enumerate(results, start=1):
                key = document.metadata.get(
                    "chunk_id",
                    f"{document.metadata.get('document_id', '')}:{document.page_content}",
                )
                score = weight / (60 + rank)
                previous = ranked.get(key)
                if previous:
                    score += previous[1]
                ranked[key] = (document, score)

        source_groups: dict[str, tuple[list[Document], float]] = {}
        for document, score in sorted(
            ranked.values(), key=lambda item: item[1], reverse=True
        ):
            source_key = document.metadata.get(
                "document_id", document.metadata.get("chunk_id", document.page_content)
            )
            documents_for_source, source_score = source_groups.get(
                source_key, ([], 0.0)
            )
            if not any(
                existing.page_content == document.page_content
                for existing in documents_for_source
            ):
                documents_for_source.append(document)
            source_groups[source_key] = (
                documents_for_source,
                max(source_score, score),
            )

        results = []
        for documents_for_source, score in sorted(
            source_groups.values(), key=lambda item: item[1], reverse=True
        )[:k]:
            primary = documents_for_source[0]
            combined = Document(
                page_content="\n\n".join(
                    document.page_content for document in documents_for_source
                ),
                metadata=primary.metadata,
            )
            results.append((combined, score))
        return results


def load_retriever(
    index_path: Path,
    api_key: str,
    model: str,
) -> HybridRetriever:
    documents_path = index_path / "documents.jsonl"
    if not documents_path.is_file():
        raise FileNotFoundError(
            f"Missing {documents_path}. Build the index with "
            "`python -m src.ingestion.build_index`."
        )

    documents = []
    with documents_path.open(encoding="utf-8") as document_file:
        for line_number, line in enumerate(document_file, start=1):
            try:
                record = json.loads(line)
                documents.append(
                    Document(
                        page_content=record["page_content"],
                        metadata=record["metadata"],
                    )
                )
            except (json.JSONDecodeError, KeyError, TypeError) as error:
                raise ValueError(
                    f"Invalid indexed document on line {line_number}."
                ) from error

    embeddings = create_embeddings(api_key, model)
    vector_store = FAISS.load_local(
        str(index_path),
        embeddings,
        allow_dangerous_deserialization=True,
    )
    return HybridRetriever(vector_store, documents)
