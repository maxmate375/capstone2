from langchain_core.documents import Document

from src.retrieval.hybrid_search import HybridRetriever


class FakeVectorStore:
    def __init__(self, documents):
        self.documents = documents

    def similarity_search(self, query, k=4):
        return self.documents[:k]


def test_hybrid_retrieval_combines_semantic_and_keyword_matches():
    semantic = Document(
        page_content="PM-KISAN eligibility applies to eligible farmer families.",
        metadata={"chunk_id": "pm-kisan"},
    )
    keyword = Document(
        page_content="PM-KISAN benefits are described on MyScheme.",
        metadata={"chunk_id": "pm-kisan-benefits"},
    )
    retriever = HybridRetriever(FakeVectorStore([semantic]), [semantic, keyword])

    results = retriever.search("PM-KISAN eligibility benefits", k=2)

    assert len(results) == 2
    assert all(score > 0 for _, score in results)


def test_hybrid_retrieval_groups_matching_chunks_by_scheme():
    first_chunk = Document(
        page_content="PM-KISAN eligibility for landholding families.",
        metadata={"document_id": "pm-kisan", "chunk_id": "pm-kisan:1"},
    )
    second_chunk = Document(
        page_content="PM-KISAN exclusion criteria include specified categories.",
        metadata={"document_id": "pm-kisan", "chunk_id": "pm-kisan:2"},
    )
    another_scheme = Document(
        page_content="A different central scholarship scheme.",
        metadata={"document_id": "scholarship", "chunk_id": "scholarship:1"},
    )
    documents = [first_chunk, second_chunk, another_scheme]
    retriever = HybridRetriever(FakeVectorStore(documents), documents)

    results = retriever.search("PM-KISAN eligibility exclusion", k=2)

    assert results[0][0].metadata["document_id"] == "pm-kisan"
    assert "landholding families" in results[0][0].page_content
    assert "exclusion criteria" in results[0][0].page_content
    assert len({document.metadata["document_id"] for document, _ in results}) == 2
