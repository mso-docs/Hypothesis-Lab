from typing import Literal
from pydantic import BaseModel, Field, model_validator


class ScientificHypothesis(BaseModel):
    statement: str = Field(min_length=10)
    scientific_domain: str = "Climate science"


class Observation(BaseModel):
    experiment_id: str
    successes: int = Field(ge=0, strict=True)
    trials: int = Field(gt=0, strict=True)
    success_definition: str = "Day exceeding a fixed extreme-heat threshold"
    synthetic: bool = True
    independently_verified: bool = False
    sampling_description: str | None = (
        "Synthetic demonstration; independent Bernoulli trials assumed"
    )
    source_publication_id: str | None = None

    @model_validator(mode="after")
    def valid_counts(self):
        if self.successes > self.trials:
            raise ValueError("Events cannot exceed eligible observations")
        return self


class Publication(BaseModel):
    id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    doi: str | None = None
    abstract: str | None = None
    url: str | None = None
    provider: str = "OpenAlex"


class Evidence(BaseModel):
    publication_id: str
    claim: str
    excerpt: str
    relationship: Literal[
        "supporting", "contradicting", "inconclusive", "unclassified"
    ] = "unclassified"
    evidence_type: Literal["qualitative"] = "qualitative"
    source_location: str = "Abstract, first sentence"
    model_identifier: str | None = None
    extraction_method: str = (
        "Verbatim abstract sentence; researcher classification required"
    )
    requires_review: bool = True
