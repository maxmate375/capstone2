from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserProfile(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    age: int | None = Field(default=None, ge=0, le=120)
    gender: str | None = Field(default=None, max_length=40)
    state: str | None = Field(default=None, max_length=80)
    annual_household_income: int | None = Field(default=None, ge=0, le=10_000_000_000)
    occupation: str | None = Field(default=None, max_length=120)
    social_category: str | None = Field(default=None, max_length=80)
    is_farmer: bool | None = None
    is_student: bool | None = None
    disability_status: bool | None = None
    bpl_household: bool | None = None


class QueryRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(min_length=3, max_length=2000)
    session_id: str | None = Field(default=None, min_length=1, max_length=128)
    profile: UserProfile | None = None


class SourceReference(BaseModel):
    title: str
    citation: str
    url: str
    official_url: str = ""
    ministry: str = ""


class SchemeMatch(BaseModel):
    scheme_name: str
    status: Literal[
        "potential_match", "needs_more_information", "may_not_match"
    ]
    rationale: str
    criteria_matched: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class QueryResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceReference]
    retrieved_context: list[str]
    eligibility_matches: list[SchemeMatch]
    agents_invoked: list[str]
    confidence: float = Field(ge=0, le=1)


class FeedbackRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    session_id: str = Field(min_length=1, max_length=128)
    query: str = Field(min_length=3, max_length=2000)
    rating: int
    correction: str | None = Field(default=None, max_length=4000)

    @field_validator("rating")
    @classmethod
    def rating_must_be_thumb(cls, value: int) -> int:
        if value not in (-1, 1):
            raise ValueError("rating must be -1 (thumbs down) or 1 (thumbs up).")
        return value


class FeedbackResponse(BaseModel):
    feedback_id: int
    status: str
