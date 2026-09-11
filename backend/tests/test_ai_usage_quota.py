import os
import unittest
import uuid
from datetime import date
from unittest.mock import patch

from app.db import get_connection
from app.services.ai_usage_quota import AiQuotaError, AiUsageQuotaService


class AiUsageQuotaContractTests(unittest.TestCase):
    def test_governed_plan_limits(self):
        service = AiUsageQuotaService(
            {"base": 3, "premium_light": 50, "premium_pro": 100, "internal": 3}
        )
        self.assertEqual(service.limits["base"], 3)
        self.assertEqual(service.limits["premium_light"], 50)
        self.assertEqual(service.limits["premium_pro"], 100)

    def test_unknown_plan_falls_back_to_base(self):
        self.assertEqual(AiUsageQuotaService.normalize_plan("unknown"), "base")

    def test_mobile_plan_cannot_grant_premium(self):
        with patch.dict(os.environ, {"WYE_RUNTIME_ENVIRONMENT": "production"}, clear=False):
            self.assertEqual(
                AiUsageQuotaService.resolve_actor_plan("premium_pro"), "base"
            )

    def test_dev_override_is_server_side_only(self):
        with patch.dict(
            os.environ,
            {
                "WYE_RUNTIME_ENVIRONMENT": "e2e",
                "WYE_PHASE9_AI_PLAN_OVERRIDE": "premium_light",
            },
            clear=False,
        ):
            self.assertEqual(
                AiUsageQuotaService.resolve_actor_plan("premium_pro"),
                "premium_light",
            )

    def test_actor_identifier_is_hashed(self):
        actor = "installation_0123456789abcdef"
        digest = AiUsageQuotaService.actor_hash(actor)
        self.assertEqual(len(digest), 64)
        self.assertNotIn(actor, digest)


@unittest.skipUnless(os.getenv("WYE_TEST_DATABASE"), "requires isolated WYE_TEST_DATABASE")
class AiUsageQuotaDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.actor = f"test_installation_{uuid.uuid4().hex}"
        self.digest = AiUsageQuotaService.actor_hash(self.actor)
        self.service = AiUsageQuotaService(
            {"base": 3, "premium_light": 50, "premium_pro": 100, "internal": 3}
        )

    def tearDown(self):
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM ai_usage_events WHERE actor_hash=%s", (self.digest,))
            connection.commit()
        finally:
            connection.close()

    def _consume(self, **overrides):
        values = {
            "actor_id": self.actor,
            "local_day": date.today(),
            "plan": "base",
            "operation": "label_text_normalization",
            "provider": "openai",
        }
        values.update(overrides)
        return self.service.consume(**values)

    def test_base_allows_three_billable_calls_then_rejects(self):
        for remaining in (2, 1, 0):
            self.assertEqual(self._consume().remaining, remaining)
        with self.assertRaises(AiQuotaError) as caught:
            self._consume()
        self.assertEqual(caught.exception.status, 429)

    def test_cache_and_non_billable_provider_do_not_consume(self):
        self._consume(cache_hit=True)
        status = self._consume(billable_provider_call=False, provider="fake")
        self.assertEqual(status.used, 0)

    def test_fake_provider_can_explicitly_simulate_billable_usage(self):
        status = self._consume(provider="fake", billable_provider_call=True)
        self.assertEqual(status.used, 1)


if __name__ == "__main__":
    unittest.main()
