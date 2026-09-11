import json
import re

from app.db import get_connection


_URL = re.compile(r"https?://\S+", re.IGNORECASE)
_BARCODE = re.compile(r"\b\d{8,14}\b")
_SECRET = re.compile(
    r"(?i)(bearer\s+|token\s*[:=]\s*|api[_-]?key\s*[:=]\s*)\S+"
)
_IMAGE_PAYLOAD = re.compile(r"(?i)data:image/[^;]+;base64,[A-Za-z0-9+/=]+")
_SAFE_CONTEXT_KEYS = {
    "app_version",
    "platform",
    "device_class",
    "route",
    "error_code",
    "test_run_id",
}


def sanitize_feedback_text(value: str | None, maximum: int) -> str | None:
    if value is None:
        return None
    cleaned = _IMAGE_PAYLOAD.sub("<redacted-image>", value)
    cleaned = _URL.sub("<redacted-url>", cleaned)
    cleaned = _SECRET.sub("<redacted-secret>", cleaned)
    cleaned = _BARCODE.sub("<redacted-number>", cleaned)
    cleaned = cleaned.strip()[:maximum]
    return cleaned or None


class BetaFeedbackService:
    def create(self, payload: dict) -> dict:
        message = sanitize_feedback_text(payload.get("message"), 4000)
        if message is None or len(message) < 5:
            raise ValueError("feedback_message_required")
        expected = sanitize_feedback_text(payload.get("expected_behavior"), 2000)
        actual = sanitize_feedback_text(payload.get("actual_behavior"), 2000)
        context = {
            key: sanitize_feedback_text(str(value), 200)
            for key, value in (payload.get("sanitized_context") or {}).items()
            if key in _SAFE_CONTEXT_KEYS and value is not None
        }
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO beta_feedback(
                      feedback_type,severity,message,expected_behavior,
                      actual_behavior,app_version,platform,device_class,route,
                      sanitized_context_json
                    ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                    RETURNING id,created_at,status
                    """,
                    (
                        payload["feedback_type"],
                        payload["severity"],
                        message,
                        expected,
                        actual,
                        sanitize_feedback_text(payload.get("app_version"), 80),
                        sanitize_feedback_text(payload.get("platform"), 40),
                        sanitize_feedback_text(payload.get("device_class"), 80),
                        sanitize_feedback_text(payload.get("route"), 120),
                        json.dumps(context) if context else None,
                    ),
                )
                row = cur.fetchone()
                conn.commit()
                return {"id": row[0], "created_at": row[1], "status": row[2]}
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
