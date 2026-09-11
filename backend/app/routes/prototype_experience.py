from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.ai_usage_quota import AiQuotaError, AiUsageQuotaService
from app.services.beta_feedback import BetaFeedbackService


router = APIRouter(prefix="/mobile/v1", tags=["mobile-prototype"])
_quota = AiUsageQuotaService()
_feedback = BetaFeedbackService()


class BetaFeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feedback_type: Literal[
        "bug", "ux_ui", "ocr", "barcode", "result_score", "performance",
        "suggestion", "other"
    ]
    severity: Literal["low", "medium", "high", "blocking"]
    message: str = Field(min_length=5, max_length=8000)
    expected_behavior: str | None = Field(default=None, max_length=4000)
    actual_behavior: str | None = Field(default=None, max_length=4000)
    app_version: str | None = Field(default=None, max_length=160)
    platform: str | None = Field(default=None, max_length=80)
    device_class: str | None = Field(default=None, max_length=160)
    route: str | None = Field(default=None, max_length=240)
    sanitized_context: dict[str, Any] | None = None

    @field_validator("sanitized_context")
    @classmethod
    def context_must_be_small(cls, value):
        if value is not None and (len(value) > 10 or any(isinstance(v, (dict, list)) for v in value.values())):
            raise ValueError("sanitized_context must contain at most 10 scalar values")
        return value


def _plan(value: str | None) -> str:
    # No production identity/subscription contract exists yet. Unknown or
    # missing client declarations therefore fail closed to Base.
    return AiUsageQuotaService.resolve_actor_plan(value)


@router.get("/ai-usage/today")
def get_ai_usage_today(
    local_day: date,
    x_wye_install_id: str = Header(alias="X-WYE-Install-ID"),
    x_wye_plan: str | None = Header(default=None, alias="X-WYE-Plan"),
):
    try:
        return _quota.status(x_wye_install_id, local_day, _plan(x_wye_plan)).as_dict()
    except AiQuotaError as exc:
        raise HTTPException(exc.status, detail={"code": exc.code, "message": exc.message}) from exc


@router.post("/beta-feedback", status_code=201)
def create_beta_feedback(payload: BetaFeedbackRequest, response: Response):
    try:
        result = _feedback.create(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(422, detail={"code": str(exc)}) from exc
    response.headers["Cache-Control"] = "no-store"
    return result


def get_ai_quota_service() -> AiUsageQuotaService:
    return _quota
