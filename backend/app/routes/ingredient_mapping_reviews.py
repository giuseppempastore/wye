from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.security import require_image_api_key
from app.services.ingredient_mapping_reviews import (
    IngredientMappingReviewError,
    IngredientMappingReviewService,
)


ReviewStatus = Literal["pending", "accepted", "ambiguous", "rejected"]
DecisionStatus = Literal["accepted", "ambiguous", "rejected"]

router = APIRouter(
    prefix="/ingredient-mapping-reviews",
    tags=["ingredient-mapping-reviews"],
    dependencies=[Depends(require_image_api_key)],
)


class ReviewDecisionRequest(BaseModel):
    status: DecisionStatus
    candidate_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_candidate(self):
        if self.status == "accepted" and self.candidate_id is None:
            raise ValueError("candidate_id is required for accepted decisions")
        if self.status != "accepted" and self.candidate_id is not None:
            raise ValueError("candidate_id is only allowed for accepted decisions")
        return self


class ReviewListItem(BaseModel):
    review_id: int
    product_ingredient_id: int
    product_id: int
    raw_text: str
    normalized_text: str | None
    detected_language: str | None
    review_status: ReviewStatus
    created_at: datetime
    candidate_count: int


class ReviewListResponse(BaseModel):
    reviews: list[ReviewListItem]


class ReviewCandidateResponse(BaseModel):
    candidate_id: int
    ingredient_id: int
    canonical_name: str
    candidate_method: str
    candidate_confidence: float | None
    rationale: str | None
    is_selected: bool


class ReviewDetailResponse(BaseModel):
    review: dict[str, Any]
    product_ingredient: dict[str, Any]
    candidates: list[ReviewCandidateResponse]


class ApprovedAlias(BaseModel):
    id: int
    ingredient_id: int
    alias_name: str
    normalized_alias: str
    language: str
    alias_type: str
    confidence: float
    is_primary: bool
    mapping_method: str
    mapping_status: str
    approved_at: datetime
    review_provenance: dict[str, Any]
    created_at: datetime


class ApprovedAliasResponse(BaseModel):
    alias: ApprovedAlias
    created: bool


def _service():
    return IngredientMappingReviewService()


def _call(function):
    try:
        return function()
    except IngredientMappingReviewError as exc:
        raise HTTPException(
            exc.status, {"code": exc.code, "message": exc.message}
        ) from exc


@router.get("", response_model=ReviewListResponse)
def list_reviews(status: ReviewStatus = "pending"):
    return _call(lambda: _service().list(status))


@router.get("/{review_id}", response_model=ReviewDetailResponse)
def get_review(review_id: int):
    return _call(lambda: _service().detail(review_id))


@router.post("/{review_id}/decision", response_model=ReviewDetailResponse)
def decide_review(review_id: int, payload: ReviewDecisionRequest):
    return _call(
        lambda: _service().decide(review_id, payload.status, payload.candidate_id)
    )

@router.post("/{review_id}/approve-alias", response_model=ApprovedAliasResponse)
def approve_review_alias(review_id: int):
    return _call(lambda: _service().approve_alias(review_id))
