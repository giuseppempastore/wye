import hashlib
import os
import re
from dataclasses import dataclass
from datetime import date

from app.db import get_connection


PLAN_NAMES = {"base", "premium_light", "premium_pro", "internal"}
SAFE_NAME = re.compile(r"^[a-z0-9_.-]{1,80}$")


class AiQuotaError(RuntimeError):
    def __init__(self, code: str, message: str, status: int = 422):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


@dataclass(frozen=True)
class AiQuotaStatus:
    plan: str
    local_day: date
    limit: int | None
    used: int

    @property
    def remaining(self) -> int | None:
        return None if self.limit is None else max(0, self.limit - self.used)

    def as_dict(self) -> dict:
        return {
            "plan": self.plan,
            "local_day": self.local_day.isoformat(),
            "limit": self.limit,
            "used": self.used,
            "remaining": self.remaining,
        }


class AiUsageQuotaService:
    def __init__(self, limits: dict[str, int | None] | None = None):
        self.limits = limits or {
            "base": self._env_limit("WYE_AI_DAILY_LIMIT_BASE", 3),
            "premium_light": self._env_limit(
                "WYE_AI_DAILY_LIMIT_PREMIUM_LIGHT", 50
            ),
            "premium_pro": self._env_limit("WYE_AI_DAILY_LIMIT_PREMIUM_PRO", 100),
            "internal": self._internal_limit(),
        }

    @staticmethod
    def _env_limit(name: str, default: int) -> int:
        value = int(os.getenv(name, str(default)))
        if value < 0 or value > 100000:
            raise RuntimeError(f"{name} is outside the allowed range")
        return value

    @staticmethod
    def _internal_limit() -> int | None:
        raw = os.getenv("WYE_AI_DAILY_LIMIT_INTERNAL", "3").strip().lower()
        if raw == "unlimited" and os.getenv("WYE_RUNTIME_ENVIRONMENT") in {
            "dev",
            "test",
            "e2e",
        }:
            return None
        value = int(raw)
        if value < 0 or value > 100000:
            raise RuntimeError("WYE_AI_DAILY_LIMIT_INTERNAL is invalid")
        return value

    @staticmethod
    def normalize_plan(plan: str | None) -> str:
        value = (plan or "base").strip().lower()
        return value if value in PLAN_NAMES else "base"

    @staticmethod
    def resolve_actor_plan(_client_plan: str | None = None) -> str:
        """Fail closed until account/subscription identity is implemented.

        A development override is accepted only in explicitly non-production
        environments; a mobile header can never grant itself a paid plan.
        """
        environment = os.getenv("WYE_RUNTIME_ENVIRONMENT", "production").lower()
        if environment in {"local", "dev", "development", "test", "e2e"}:
            override = os.getenv("WYE_PHASE9_AI_PLAN_OVERRIDE")
            if override:
                return AiUsageQuotaService.normalize_plan(override)
        return "base"

    @staticmethod
    def actor_hash(actor_id: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9._-]{16,128}", actor_id or ""):
            raise AiQuotaError("invalid_installation_id", "Installation ID is invalid")
        return hashlib.sha256(actor_id.encode("utf-8")).hexdigest()

    def status(self, actor_id: str, local_day: date, plan: str | None) -> AiQuotaStatus:
        normalized_plan = self.normalize_plan(plan)
        digest = self.actor_hash(actor_id)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COALESCE(SUM(cost_units),0)
                    FROM ai_usage_events
                    WHERE actor_hash=%s AND local_day=%s AND status='consumed'
                    """,
                    (digest, local_day),
                )
                used = int(cur.fetchone()[0])
            return AiQuotaStatus(normalized_plan, local_day, self.limits[normalized_plan], used)
        finally:
            conn.close()

    def consume(
        self,
        *,
        actor_id: str,
        local_day: date,
        plan: str | None,
        operation: str,
        provider: str,
        model: str | None = None,
        cost_units: int = 1,
        cache_hit: bool = False,
        billable_provider_call: bool = True,
    ) -> AiQuotaStatus:
        if not SAFE_NAME.fullmatch(operation) or not SAFE_NAME.fullmatch(provider):
            raise AiQuotaError("invalid_usage_metadata", "Usage metadata is invalid")
        if cost_units < 0 or cost_units > 1000:
            raise AiQuotaError("invalid_cost_units", "Cost units are invalid")
        normalized_plan = self.normalize_plan(plan)
        digest = self.actor_hash(actor_id)
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT pg_advisory_xact_lock(hashtext(%s))",
                    (f"{digest}:{local_day.isoformat()}",),
                )
                cur.execute(
                    """
                    SELECT COALESCE(SUM(cost_units),0)
                    FROM ai_usage_events
                    WHERE actor_hash=%s AND local_day=%s AND status='consumed'
                    """,
                    (digest, local_day),
                )
                used = int(cur.fetchone()[0])
                limit = self.limits[normalized_plan]
                should_consume = billable_provider_call and not cache_hit and cost_units > 0
                if should_consume and limit is not None and used + cost_units > limit:
                    cur.execute(
                        """
                        INSERT INTO ai_usage_events(
                          local_day,actor_hash,plan,operation,provider,model,
                          cost_units,cache_hit,status,sanitized_error_code
                        ) VALUES(%s,%s,%s,%s,%s,%s,0,%s,'quota_rejected','daily_limit_reached')
                        """,
                        (local_day, digest, normalized_plan, operation, provider, model, cache_hit),
                    )
                    conn.commit()
                    raise AiQuotaError(
                        "daily_ai_limit_reached",
                        "Daily external AI limit reached",
                        429,
                    )
                cur.execute(
                    """
                    INSERT INTO ai_usage_events(
                      local_day,actor_hash,plan,operation,provider,model,
                      cost_units,cache_hit,status
                    ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        local_day,
                        digest,
                        normalized_plan,
                        operation,
                        provider,
                        model,
                        cost_units if should_consume else 0,
                        cache_hit,
                        "consumed" if should_consume else "not_billable",
                    ),
                )
                if should_consume:
                    used += cost_units
                conn.commit()
                return AiQuotaStatus(normalized_plan, local_day, limit, used)
        except AiQuotaError:
            raise
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
