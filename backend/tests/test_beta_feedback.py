import os
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.db import get_connection
from app.routes.prototype_experience import router
from app.services.beta_feedback import BetaFeedbackService, sanitize_feedback_text


class BetaFeedbackSanitizationTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)

    def test_redacts_sensitive_values(self):
        raw = (
            "Bearer secret-value barcode 4006381333931 "
            "https://storage.example/presigned?secret=yes "
            "data:image/png;base64,AAAA"
        )
        sanitized = sanitize_feedback_text(raw, 4000)
        self.assertNotIn("secret-value", sanitized)
        self.assertNotIn("4006381333931", sanitized)
        self.assertNotIn("storage.example", sanitized)
        self.assertNotIn("AAAA", sanitized)

    def test_empty_feedback_is_rejected_before_database_write(self):
        with self.assertRaises(ValueError):
            BetaFeedbackService().create(
                {"feedback_type": "bug", "severity": "low", "message": "   "}
            )

    def test_create_feedback_endpoint_accepts_valid_payload(self):
        with patch("app.routes.prototype_experience._feedback.create") as create:
            create.return_value = {"id": 12, "status": "new"}
            response = self.client.post(
                "/mobile/v1/beta-feedback",
                json={
                    "feedback_type": "bug",
                    "severity": "blocking",
                    "message": "La fotocamera non risponde",
                },
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "new")

    def test_feedback_endpoint_rejects_short_and_oversized_messages(self):
        for message in ("no", "x" * 8001):
            response = self.client.post(
                "/mobile/v1/beta-feedback",
                json={
                    "feedback_type": "bug",
                    "severity": "low",
                    "message": message,
                },
            )
            self.assertEqual(response.status_code, 422)


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated WYE_TEST_DATABASE")
class BetaFeedbackDatabaseTests(unittest.TestCase):
    def test_feedback_is_sanitized_and_persisted(self):
        result = BetaFeedbackService().create(
            {
                "feedback_type": "ux_ui",
                "severity": "high",
                "message": "La schermata mostra Bearer hidden-value e 4006381333931",
                "sanitized_context": {
                    "route": "/feedback",
                    "prompt": "must-not-be-stored",
                },
            }
        )
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT message,sanitized_context_json FROM beta_feedback WHERE id=%s",
                    (result["id"],),
                )
                message, context = cursor.fetchone()
                self.assertNotIn("hidden-value", message)
                self.assertNotIn("4006381333931", message)
                self.assertEqual(context, {"route": "/feedback"})
                cursor.execute("DELETE FROM beta_feedback WHERE id=%s", (result["id"],))
            connection.commit()
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
