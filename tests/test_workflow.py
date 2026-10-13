from langchain_core.documents import Document
from langchain_core.messages import AIMessage

from src.agents.workflow import (
    AgenticRAGWorkflow,
    EligibilityReview,
    GroundingVerdict,
    SchemeEligibilityMatch,
)


class FakeRetriever:
    def __init__(self):
        self.requested_k = []
        self.document = Document(
            page_content=(
                "Eligibility criteria: Applicants must meet the criteria stated "
                "in the official scheme guidelines."
            ),
            metadata={
                "chunk_id": "scheme-1",
                "title": "Central scheme",
                "source": "MyScheme",
                "url": "https://www.myscheme.gov.in/schemes/example",
            },
        )

    def search(self, query, k):
        self.requested_k.append(k)
        return [(self.document, 0.02)]


class EmptyRetriever:
    def search(self, query, k):
        return []


class FakeValidator:
    def __init__(self, owner, schema):
        self.owner = owner
        self.schema = schema

    def invoke(self, prompt):
        if self.schema is EligibilityReview:
            return EligibilityReview(
                matches=[
                    SchemeEligibilityMatch(
                        scheme_name="Central scheme",
                        status="needs_more_information",
                        rationale="The profile does not contain all required details.",
                        missing_information=["Official criteria confirmation"],
                    )
                ]
            )
        return self.owner.verdicts.pop(0)


class FakeLLM:
    def __init__(self, verdicts):
        self.verdicts = list(verdicts)
        self.prompts = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return AIMessage(content="Please check the official eligibility criteria.")

    def with_structured_output(self, schema):
        return FakeValidator(self, schema)


def verdict(grounded):
    return GroundingVerdict(
        grounded=grounded,
        confidence=0.9 if grounded else 0.2,
        reason="Evidence check",
    )


def test_failed_grounding_retries_and_delegates_eligibility_assessment():
    retriever = FakeRetriever()
    llm = FakeLLM([verdict(False), verdict(True)])
    workflow = AgenticRAGWorkflow(retriever, llm, max_retries=1)

    result = workflow.invoke(
        "Which central schemes may I qualify for?",
        "retry-session",
        profile={"age": 30, "state": "Maharashtra", "is_farmer": True},
    )

    assert retriever.requested_k == [4, 8]
    assert result["attempts"] == 1
    assert "query_rewriter" in result["agents_invoked"]
    assert "eligibility_assessment_agent" in result["agents_invoked"]
    assert result["eligibility_matches"][0]["status"] == "needs_more_information"
    assert result["validation_passed"] is True


def test_session_history_is_kept_but_agent_trace_is_per_turn():
    retriever = FakeRetriever()
    llm = FakeLLM([verdict(True), verdict(True)])
    workflow = AgenticRAGWorkflow(retriever, llm)

    first = workflow.invoke("What does this scheme provide?", "history-session")
    second = workflow.invoke("Can you summarize the scheme again?", "history-session")

    assert first["agents_invoked"] == [
        "planner",
        "retriever",
        "consultation_agent",
        "validator",
        "finalize",
    ]
    assert second["agents_invoked"] == first["agents_invoked"]
    assert len(second["conversation_history"]) == 2
    assert "What does this scheme provide?" in llm.prompts[-1]


def test_empty_retrieval_returns_safe_no_evidence_answer():
    llm = FakeLLM([])
    workflow = AgenticRAGWorkflow(EmptyRetriever(), llm, max_retries=0)

    result = workflow.invoke("A question with no scheme match", "empty-session")

    assert result["validation_passed"] is False
    assert result["confidence"] == 0.0
    assert result["answer"].startswith(
        "I could not verify an answer in the available central government scheme"
    )
    assert "not an official approval" in result["answer"]
    assert result["profile"] == {}


def test_profile_is_not_retained_in_session_checkpointer():
    retriever = FakeRetriever()
    llm = FakeLLM([verdict(True)])
    workflow = AgenticRAGWorkflow(retriever, llm)

    result = workflow.invoke(
        "Tell me about this scheme",
        "private-profile",
        profile={"age": 25, "state": "Karnataka"},
    )

    assert result["profile"] == {}
    assert "eligibility_assessment_agent" in result["agents_invoked"]


def test_unverified_match_is_removed_with_safe_fallback():
    retriever = FakeRetriever()
    llm = FakeLLM([verdict(False)])
    workflow = AgenticRAGWorkflow(retriever, llm, max_retries=0)

    result = workflow.invoke(
        "Can I qualify for this scheme?",
        "unverified-match",
        profile={"age": 35, "is_farmer": True},
    )

    assert result["validation_passed"] is False
    assert result["eligibility_matches"] == []
    assert result["answer"].startswith(
        "I could not verify an answer in the available central government scheme"
    )
