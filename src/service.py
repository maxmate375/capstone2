from langchain_openai import ChatOpenAI

from src.agents.workflow import AgenticRAGWorkflow
from src.config import Settings
from src.retrieval.hybrid_search import HybridRetriever, load_retriever

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class GovernmentSchemesAssistant:
    def __init__(self, workflow: AgenticRAGWorkflow, retriever: HybridRetriever, llm):
        self.workflow = workflow
        self.retriever = retriever
        self.llm = llm

    def query(
        self, query: str, session_id: str, profile: dict | None = None
    ) -> dict:
        result = self.workflow.invoke(query, session_id, profile=profile)
        documents = result.get("retrieved_documents", [])
        return {
            "answer": result["answer"],
            "sources": [
                {
                    "title": item["metadata"].get("title", "Government scheme"),
                    "citation": item["metadata"].get("source", "Unknown source"),
                    "url": item["metadata"].get("url", ""),
                    "official_url": item["metadata"].get("official_url", ""),
                    "ministry": item["metadata"].get("ministry", ""),
                }
                for item in documents
            ],
            "retrieved_context": [
                item["page_content"] for item in documents
            ],
            "eligibility_matches": result.get("eligibility_matches", []),
            "agents_invoked": result.get("agents_invoked", []),
            "confidence": result.get("confidence", 0.0),
        }

    def baseline_answer(self, query: str) -> tuple[str, list[str]]:
        results = self.retriever.search(query, k=4)
        context = "\n\n".join(document.page_content for document, _ in results)
        answer = self.llm.invoke(
            "Answer the question only from the retrieved Indian central "
            "government scheme context. If there is not enough evidence, say so. "
            "Do not make a definitive eligibility decision.\n\n"
            f"Question: {query}\nContext:\n{context}"
        )
        content = getattr(answer, "content", answer)
        if not isinstance(content, str):
            raise TypeError("The language model returned a non-text response.")
        return content.strip(), [document.page_content for document, _ in results]


def build_assistant(settings: Settings) -> GovernmentSchemesAssistant:
    if not settings.openrouter_api_key:
        raise RuntimeError(
            "Set OPENROUTER_API_KEY in your .env file. "
            "Get a free key at https://openrouter.ai/keys"
        )

    llm = ChatOpenAI(
        model=settings.openrouter_chat_model,
        base_url=OPENROUTER_BASE_URL,
        api_key=settings.openrouter_api_key,
        temperature=0,
        default_headers={
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Bharat Scheme Saathi",
        },
    )

    retriever = load_retriever(
        settings.index_path,
        settings.openrouter_api_key,
        settings.openrouter_embedding_model,
    )

    workflow = AgenticRAGWorkflow(
        retriever,
        llm,
        max_retries=settings.max_retrieval_retries,
    )
    return GovernmentSchemesAssistant(workflow, retriever, llm)
