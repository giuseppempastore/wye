import os
import unittest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.mobile_upload import (
    get_image_upload_service,
    get_label_extraction_service,
    get_mobile_session_store,
    router,
)
from app.services.mobile_upload_sessions import (
    MobileSessionError,
    MobileUploadSessionStore,
)


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 9, 3, 10, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.now

    def advance(self, seconds: int):
        self.now += timedelta(seconds=seconds)


class MobileUploadFacadeTests(unittest.TestCase):
    environment_names = (
        "WYE_MOBILE_UPLOAD_FACADE_ENABLED",
        "WYE_MOBILE_UPLOAD_FACADE_SESSION_TTL_SECONDS",
        "WYE_IMAGE_API_KEY",
    )

    def setUp(self):
        self.original_environment = {
            name: os.environ.get(name) for name in self.environment_names
        }
        for name in self.environment_names:
            os.environ.pop(name, None)

        self.clock = FakeClock()
        self.store = MobileUploadSessionStore(clock=self.clock)
        self.upload_service = Mock()
        self.extraction_service = Mock()

        app = FastAPI()
        app.include_router(router)
        app.dependency_overrides[get_mobile_session_store] = lambda: self.store
        app.dependency_overrides[get_image_upload_service] = (
            lambda: self.upload_service
        )
        app.dependency_overrides[get_label_extraction_service] = (
            lambda: self.extraction_service
        )
        self.client = TestClient(app)

    def tearDown(self):
        for name, value in self.original_environment.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def _enable(self):
        os.environ["WYE_MOBILE_UPLOAD_FACADE_ENABLED"] = "true"
        os.environ["WYE_IMAGE_API_KEY"] = "operator-secret"

    def _create_session(self, scopes=None):
        payload = {} if scopes is None else {"scopes": scopes}
        response = self.client.post(
            "/mobile/dev/v1/capture/sessions",
            json=payload,
            headers={"X-WYE-Image-Key": "operator-secret"},
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response

    @staticmethod
    def _upload_payload():
        return {
            "image_type": "ingredients",
            "mime_type": "image/jpeg",
            "byte_size": 128,
            "sha256": "a" * 64,
        }

    @staticmethod
    def _bearer(token):
        return {"Authorization": f"Bearer {token}"}

    def test_facade_is_disabled_by_default_for_all_entry_types(self):
        upload_id = uuid.uuid4()
        requests = (
            self.client.post(
                "/mobile/dev/v1/capture/sessions",
                json={},
                headers={"X-WYE-Image-Key": "unused"},
            ),
            self.client.post(
                "/mobile/dev/v1/capture/products/7/images/uploads",
                json=self._upload_payload(),
                headers={"Authorization": "Bearer unused"},
            ),
            self.client.post(
                f"/mobile/dev/v1/capture/products/7/images/uploads/{upload_id}/finalize",
                headers={"Authorization": "Bearer unused"},
            ),
            self.client.post(
                "/mobile/dev/v1/capture/products/7/images/8/extractions",
                json={},
                headers={"Authorization": "Bearer unused"},
            ),
            self.client.get(
                "/mobile/dev/v1/capture/products/7/images/8/extractions",
                headers={"Authorization": "Bearer unused"},
            ),
            self.client.get(
                "/mobile/dev/v1/capture/products/7/images/8/extractions/9",
                headers={"Authorization": "Bearer unused"},
            ),
        )
        for response in requests:
            self.assertEqual(response.status_code, 503, response.text)
            self.assertEqual(
                response.json()["detail"]["code"], "mobile_facade_disabled"
            )
        self.upload_service.initialize.assert_not_called()
        self.upload_service.finalize.assert_not_called()
        self.extraction_service.create.assert_not_called()
        self.extraction_service.list.assert_not_called()
        self.extraction_service.get.assert_not_called()

    def test_router_is_registered_in_main_application(self):
        from app.main import app

        paths = {route.path for route in app.routes}
        self.assertIn("/mobile/dev/v1/capture/sessions", paths)
        self.assertIn(
            "/mobile/dev/v1/capture/products/{product_id}/images/uploads",
            paths,
        )

    def test_session_creation_requires_existing_server_authorization(self):
        os.environ["WYE_MOBILE_UPLOAD_FACADE_ENABLED"] = "true"

        unavailable = self.client.post(
            "/mobile/dev/v1/capture/sessions", json={}
        )
        self.assertEqual(unavailable.status_code, 503)
        self.assertEqual(
            unavailable.json()["detail"]["code"],
            "mobile_facade_operator_auth_unavailable",
        )

        os.environ["WYE_IMAGE_API_KEY"] = "operator-secret"
        invalid = self.client.post(
            "/mobile/dev/v1/capture/sessions",
            json={},
            headers={"X-WYE-Image-Key": "wrong"},
        )
        self.assertEqual(invalid.status_code, 401)
        self.assertEqual(
            invalid.json()["detail"]["code"],
            "mobile_facade_operator_auth_invalid",
        )

        created = self._create_session()
        body = created.json()
        self.assertEqual(body["token_type"], "Bearer")
        self.assertEqual(body["scopes"], ["extraction", "upload"])
        self.assertEqual(created.headers["cache-control"], "no-store")
        self.assertNotIn("operator-secret", created.text)
        self.assertNotIn(body["access_token"], repr(self.store._records))

    def test_invalid_config_and_out_of_bounds_ttl_fail_closed(self):
        os.environ["WYE_IMAGE_API_KEY"] = "operator-secret"
        os.environ["WYE_MOBILE_UPLOAD_FACADE_ENABLED"] = "not-a-boolean"
        invalid_flag = self.client.post(
            "/mobile/dev/v1/capture/sessions",
            json={},
            headers={"X-WYE-Image-Key": "operator-secret"},
        )
        self.assertEqual(invalid_flag.status_code, 503)
        self.assertEqual(
            invalid_flag.json()["detail"]["code"],
            "mobile_facade_unavailable",
        )

        os.environ["WYE_MOBILE_UPLOAD_FACADE_ENABLED"] = "true"
        for ttl in (29, 901):
            with self.subTest(ttl=ttl):
                os.environ[
                    "WYE_MOBILE_UPLOAD_FACADE_SESSION_TTL_SECONDS"
                ] = str(ttl)
                response = self.client.post(
                    "/mobile/dev/v1/capture/sessions",
                    json={},
                    headers={"X-WYE-Image-Key": "operator-secret"},
                )
                self.assertEqual(response.status_code, 503)
                self.assertEqual(
                    response.json()["detail"]["code"],
                    "mobile_facade_unavailable",
                )

    def test_session_repr_is_redacted_and_restart_invalidates_token(self):
        first_store = MobileUploadSessionStore(
            clock=self.clock, token_factory=lambda: "raw-mobile-capability"
        )
        issued = first_store.issue({"upload"}, 30)
        self.assertNotIn(issued.token, repr(issued))
        self.assertNotIn(issued.token, repr(first_store._records))

        restarted_store = MobileUploadSessionStore(clock=self.clock)
        with self.assertRaises(MobileSessionError) as context:
            restarted_store.validate(issued.token, "upload")
        self.assertEqual(context.exception.code, "mobile_session_invalid")

        for ttl in (29, 901):
            with self.subTest(ttl=ttl):
                with self.assertRaises(MobileSessionError) as ttl_context:
                    first_store.issue({"upload"}, ttl)
                self.assertEqual(
                    ttl_context.exception.code, "mobile_session_ttl_invalid"
                )

    def test_missing_invalid_and_expired_mobile_tokens_are_rejected(self):
        self._enable()
        token = self._create_session().json()["access_token"]
        path = "/mobile/dev/v1/capture/products/7/images/uploads"

        missing = self.client.post(path, json=self._upload_payload())
        invalid = self.client.post(
            path,
            json=self._upload_payload(),
            headers={"Authorization": "Bearer invalid"},
        )
        self.clock.advance(301)
        expired = self.client.post(
            path, json=self._upload_payload(), headers=self._bearer(token)
        )

        self.assertEqual(missing.status_code, 401)
        self.assertEqual(
            missing.json()["detail"]["code"], "mobile_session_missing"
        )
        self.assertEqual(invalid.status_code, 401)
        self.assertEqual(
            invalid.json()["detail"]["code"], "mobile_session_invalid"
        )
        self.assertEqual(expired.status_code, 401)
        self.assertEqual(
            expired.json()["detail"]["code"], "mobile_session_expired"
        )
        self.upload_service.initialize.assert_not_called()

    def test_mobile_operation_rejects_image_key_even_with_valid_session(self):
        self._enable()
        token = self._create_session().json()["access_token"]
        headers = self._bearer(token)
        headers["X-WYE-Image-Key"] = "operator-secret"

        response = self.client.post(
            "/mobile/dev/v1/capture/products/7/images/uploads",
            json=self._upload_payload(),
            headers=headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"]["code"],
            "mobile_server_secret_header_forbidden",
        )
        self.upload_service.initialize.assert_not_called()

    def test_valid_upload_scope_initializes_and_finalizes_distinct_ids(self):
        self._enable()
        token = self._create_session(["upload"]).json()["access_token"]
        upload_id = uuid.uuid4()
        signed_url = (
            "https://storage.invalid/wye/object"
            "?X-Amz-Signature=never-log-this-signature"
        )
        self.upload_service.initialize.return_value = {
            "upload_id": str(upload_id),
            "upload_url": signed_url,
            "method": "PUT",
            "headers": {"Content-Type": "image/jpeg"},
            "expires_at": self.clock.now + timedelta(minutes=5),
        }
        self.upload_service.finalize.return_value = {
            "upload_id": str(upload_id),
            "status": "finalized",
            "storage_object_id": 301,
            "product_image_id": 401,
        }

        with self.assertLogs("app.routes.mobile_upload", level="INFO") as logs:
            initialized = self.client.post(
                "/mobile/dev/v1/capture/products/7/images/uploads",
                json=self._upload_payload(),
                headers={**self._bearer(token), "X-Request-ID": "flow-1"},
            )
            finalized = self.client.post(
                f"/mobile/dev/v1/capture/products/7/images/uploads/{upload_id}/finalize",
                headers={**self._bearer(token), "X-Request-ID": "flow-2"},
            )

        self.assertEqual(initialized.status_code, 201, initialized.text)
        self.assertEqual(finalized.status_code, 200, finalized.text)
        self.upload_service.initialize.assert_called_once_with(
            7, "ingredients", "image/jpeg", 128, "a" * 64
        )
        self.upload_service.finalize.assert_called_once_with(7, str(upload_id))
        self.assertEqual(finalized.json()["storage_object_id"], 301)
        self.assertEqual(finalized.json()["product_image_id"], 401)
        self.assertNotEqual(
            finalized.json()["storage_object_id"],
            finalized.json()["product_image_id"],
        )

        captured_logs = "\n".join(logs.output)
        self.assertNotIn(token, captured_logs)
        self.assertNotIn(signed_url, captured_logs)
        self.assertNotIn("never-log-this-signature", captured_logs)
        self.assertNotIn("operator-secret", captured_logs)

    def test_upload_capability_rejects_forbidden_response_headers(self):
        self._enable()
        token = self._create_session(["upload"]).json()["access_token"]
        self.upload_service.initialize.return_value = {
            "upload_id": str(uuid.uuid4()),
            "upload_url": "https://storage.invalid/upload?signature=temporary",
            "method": "PUT",
            "headers": {"X-WYE-Image-Key": "must-not-leave-server"},
            "expires_at": self.clock.now + timedelta(minutes=5),
        }

        with self.assertLogs("app.routes.mobile_upload", level="INFO") as logs:
            response = self.client.post(
                "/mobile/dev/v1/capture/products/7/images/uploads",
                json=self._upload_payload(),
                headers=self._bearer(token),
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["detail"]["code"],
            "mobile_upload_contract_invalid",
        )
        self.assertNotIn("must-not-leave-server", response.text)
        captured_logs = "\n".join(logs.output)
        self.assertNotIn("must-not-leave-server", captured_logs)
        self.assertNotIn("signature=temporary", captured_logs)
        self.assertNotIn("status=created", captured_logs)

    def test_unexpected_upload_error_is_structured_and_redacted(self):
        self._enable()
        token = self._create_session(["upload"]).json()["access_token"]
        sensitive_error = (
            "provider rejected https://storage.invalid/upload"
            "?signature=must-not-be-logged"
        )
        self.upload_service.initialize.side_effect = RuntimeError(sensitive_error)

        with self.assertLogs("app.routes.mobile_upload", level="INFO") as logs:
            response = self.client.post(
                "/mobile/dev/v1/capture/products/7/images/uploads",
                json=self._upload_payload(),
                headers=self._bearer(token),
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["code"], "mobile_upload_failed")
        self.assertNotIn("must-not-be-logged", response.text)
        self.assertNotIn("must-not-be-logged", "\n".join(logs.output))

    def test_scope_is_enforced_and_extraction_reuses_existing_service(self):
        self._enable()
        upload_token = self._create_session(["upload"]).json()["access_token"]
        extraction_path = (
            "/mobile/dev/v1/capture/products/7/images/401/extractions"
        )

        denied = self.client.post(
            extraction_path,
            json={},
            headers={
                **self._bearer(upload_token),
                "Idempotency-Key": "extract-1",
            },
        )
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(
            denied.json()["detail"]["code"], "mobile_session_scope_denied"
        )

        extraction_token = self._create_session(["extraction"]).json()[
            "access_token"
        ]
        self.extraction_service.create.return_value = {
            "extraction": {
                "id": 501,
                "run_status": "succeeded",
                "raw_response": {"provider": "must-not-leave-facade"},
                "idempotency_key": "must-not-leave-facade",
                "error_detail": "must-not-leave-facade",
            },
            "items": [
                {
                    "id": 601,
                    "item_type": "ingredient",
                    "raw_text": "sale",
                    "extraction_status": "detected",
                    "internal_field": "must-not-leave-facade",
                }
            ],
        }
        completed = self.client.post(
            extraction_path,
            json={},
            headers={
                **self._bearer(extraction_token),
                "Idempotency-Key": "extract-1",
            },
        )

        self.assertEqual(completed.status_code, 201, completed.text)
        self.assertEqual(completed.json()["extraction"]["id"], 501)
        self.assertNotIn("raw_response", completed.json()["extraction"])
        self.assertNotIn("idempotency_key", completed.json()["extraction"])
        self.assertNotIn("error_detail", completed.json()["extraction"])
        self.assertNotIn("internal_field", completed.json()["items"][0])
        self.extraction_service.create.assert_called_once_with(
            7, 401, "extract-1", None, "label_extraction_v1"
        )

        self.extraction_service.list.return_value = {
            "extractions": [{"id": 501, "run_status": "succeeded"}]
        }
        self.extraction_service.get.return_value = {
            "extraction": {"id": 501, "run_status": "succeeded"},
            "items": [],
        }
        listed = self.client.get(
            extraction_path, headers=self._bearer(extraction_token)
        )
        retrieved = self.client.get(
            f"{extraction_path}/501", headers=self._bearer(extraction_token)
        )
        self.assertEqual(listed.status_code, 200, listed.text)
        self.assertEqual(retrieved.status_code, 200, retrieved.text)
        self.extraction_service.list.assert_called_once_with(7, 401)
        self.extraction_service.get.assert_called_once_with(7, 401, 501)

    def test_facade_does_not_invoke_scoring(self):
        self._enable()
        token = self._create_session(["upload"]).json()["access_token"]
        self.upload_service.initialize.return_value = {
            "upload_id": str(uuid.uuid4()),
            "upload_url": "https://storage.invalid/upload?signature=redacted",
            "method": "PUT",
            "headers": {"Content-Type": "image/jpeg"},
            "expires_at": self.clock.now + timedelta(minutes=5),
        }

        with patch("app.services.scoring.score_product") as score_product:
            response = self.client.post(
                "/mobile/dev/v1/capture/products/7/images/uploads",
                json=self._upload_payload(),
                headers=self._bearer(token),
            )

        self.assertEqual(response.status_code, 201, response.text)
        score_product.assert_not_called()


if __name__ == "__main__":
    unittest.main()
