import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str | None
    openrouter_chat_model: str
    openrouter_embedding_model: str
    index_path: Path
    knowledge_base_path: Path
    feedback_db_path: Path
    max_retrieval_retries: int


def _project_path(value: str, default: str) -> Path:
    path = Path(value or default)
    return path if path.is_absolute() else PROJECT_ROOT / path


def get_settings() -> Settings:
    retries = int(os.getenv("MAX_RETRIEVAL_RETRIES", "1"))
    if retries < 0 or retries > 3:
        raise ValueError("MAX_RETRIEVAL_RETRIES must be between 0 and 3.")

    return Settings(
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", "").strip() or None,
        openrouter_chat_model=os.getenv(
            "OPENROUTER_CHAT_MODEL", "google/gemini-2.0-flash-001"
        ),
        openrouter_embedding_model=os.getenv(
            "OPENROUTER_EMBEDDING_MODEL", "openai/text-embedding-3-small"
        ),
        index_path=_project_path(os.getenv("FAISS_INDEX_PATH", ""), "faiss_index"),
        knowledge_base_path=_project_path(
            os.getenv("KNOWLEDGE_BASE_PATH", ""), "data/central_schemes.jsonl"
        ),
        feedback_db_path=_project_path(
            os.getenv("FEEDBACK_DB_PATH", ""), "data/feedback.sqlite3"
        ),
        max_retrieval_retries=retries,
    )
