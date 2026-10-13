import logging
from functools import lru_cache
from typing import Annotated
from uuid import uuid4

import truststore
from fastapi import Depends, FastAPI, HTTPException

from api.schemas import (
    FeedbackRequest,
    FeedbackResponse,
    QueryRequest,
    QueryResponse,
)
from src.config import get_settings
from src.service import GovernmentSchemesAssistant, build_assistant
from src.tools.feedback_store import FeedbackStore

truststore.inject_into_ssl()

logger = logging.getLogger(__name__)
app = FastAPI(
    title="Bharat Scheme Saathi API",
    version="1.0.0",
    description=(
        "A source-grounded assistant for Indian central government schemes. "
        "Eligibility responses are preliminary; verify details with the official scheme."
    ),
)


@lru_cache
def get_assistant() -> GovernmentSchemesAssistant:
    try:
        return build_assistant(get_settings())
    except (FileNotFoundError, RuntimeError) as error:
        logger.error("Assistant is not configured: %s", error)
        raise HTTPException(status_code=503, detail=str(error)) from error


def get_feedback_store() -> FeedbackStore:
    return FeedbackStore(get_settings().feedback_db_path)


@app.get("/")
def home() -> dict[str, str]:
    return {"message": "Government schemes assistant API is running."}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/query", response_model=QueryResponse)
def query(
    request: QueryRequest,
) -> QueryResponse:
    session_id = request.session_id or str(uuid4())
    assistant = get_assistant()
    result = assistant.query(
        request.query,
        session_id,
        profile=request.profile.model_dump(exclude_none=True) if request.profile else None,
    )
    return QueryResponse(session_id=session_id, **result)


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(
    request: FeedbackRequest,
    store: Annotated[FeedbackStore, Depends(get_feedback_store)],
) -> FeedbackResponse:
    feedback_id = store.save(
        request.session_id,
        request.query,
        request.rating,
        request.correction,
    )
    return FeedbackResponse(feedback_id=feedback_id, status="recorded")
