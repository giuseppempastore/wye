import io
import logging
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import requests
from moto.server import ThreadedMotoServer

from app.extraction.config import ExtractionSettings
from app.extraction.models import ExtractionRequest, LabelExtractionOutput
from app.extraction.providers import FakeExtractionProvider
from app.services.label_extractions import provider_from_settings
from app.storage.config import StorageSettings
from app.storage.s3 import S3StorageAdapter


class FakeExtractionRuntimeTests(unittest.TestCase):
    def _settings(self, provider: str, environment: str | None):
        values = {"WYE_EXTRACTION_PROVIDER": provider}
        if environment is not None:
            values["WYE_RUNTIME_ENVIRONMENT"] = environment
        with patch.dict(os.environ, values, clear=True):
            return ExtractionSettings.from_env()

    def test_openai_remains_valid_in_production(self):
        settings = self._settings("openai", "production")
        self.assertEqual(settings.provider, "openai")
        self.assertEqual(settings.runtime_environment, "production")
        with patch(
            "app.services.label_extractions.OpenAIExtractionProvider"
        ) as provider_class:
            provider_from_settings(settings)
        provider_class.assert_called_once_with("", 90)

    def test_fake_is_valid_only_in_explicit_local_runtime_modes(self):
        for environment in ("local", "dev", "development", "test", "e2e"):
            with self.subTest(environment=environment):
                settings = self._settings("fake", environment)
                self.assertIsNone(settings.openai_api_key)
                self.assertIsInstance(
                    provider_from_settings(settings), FakeExtractionProvider
                )

    def test_fake_fails_closed_in_default_and_prod_like_modes(self):
        for environment in (None, "staging", "production"):
            with self.subTest(environment=environment):
                with self.assertRaises(RuntimeError):
                    self._settings("fake", environment)

    def test_factory_rechecks_runtime_mode(self):
        settings = ExtractionSettings(
            provider="fake",
            openai_api_key=None,
            model="wye-local-e2e-fake-v1",
            timeout_seconds=90,
            runtime_environment="production",
        )
        with self.assertRaises(RuntimeError):
            provider_from_settings(settings)

    def test_fake_returns_valid_deterministic_outputs_without_external_client(self):
        with patch(
            "app.services.label_extractions.OpenAIExtractionProvider"
        ) as external_provider:
            provider = provider_from_settings(self._settings("fake", "e2e"))
            for document_type in ("ingredients", "nutrition"):
                with self.subTest(document_type=document_type):
                    request = ExtractionRequest(
                        image_bytes=b"local-test-image",
                        mime_type="image/jpeg",
                        document_type=document_type,
                        model="wye-local-e2e-fake-v1",
                        prompt_version="label_extraction_v1",
                        schema_version="1",
                        instructions="local test only",
                        output_schema={"type": "object"},
                    )
                    result = provider.extract(request)
                    output = LabelExtractionOutput.model_validate(result.output)
                    self.assertEqual(output.document_type, document_type)
                    self.assertEqual(result.raw_response, {"fake": True})
        external_provider.assert_not_called()


class MotoLocalS3ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.werkzeug_logger = logging.getLogger("werkzeug")
        cls.werkzeug_logger_disabled = cls.werkzeug_logger.disabled
        cls.werkzeug_logger.disabled = True
        cls.server = ThreadedMotoServer(
            ip_address="127.0.0.1", port=0, verbose=False
        )
        cls.server.start()
        host, port = cls.server.get_host_and_port()
        cls.settings = StorageSettings(
            provider="s3",
            endpoint=f"http://{host}:{port}",
            bucket="wye-local-e2e-test",
            region="us-east-1",
            access_key="local-test",
            secret_key="local-test",
            force_path_style=True,
            upload_ttl=300,
            read_ttl=300,
            max_image_bytes=1024 * 1024,
            cleanup_after=1800,
        )
        cls.adapter = S3StorageAdapter(cls.settings)
        cls.adapter.client.create_bucket(Bucket=cls.settings.bucket)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        cls.werkzeug_logger.disabled = cls.werkzeug_logger_disabled

    def test_presigned_put_metadata_download_and_read_round_trip(self):
        content = b"local-moto-smoke"
        target = self.adapter.create_upload(
            "smoke/local-object.bin", "application/octet-stream", 60
        )
        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()
        with redirect_stdout(captured_stdout), redirect_stderr(captured_stderr):
            response = requests.put(
                target.url,
                data=content,
                headers=target.headers,
                timeout=10,
            )
            self.assertLess(response.status_code, 300)

            metadata = self.adapter.head_object("smoke/local-object.bin")
            self.assertIsNotNone(metadata)
            self.assertEqual(metadata.byte_size, len(content))

            downloaded = io.BytesIO()
            self.adapter.download_to("smoke/local-object.bin", downloaded)
            self.assertEqual(downloaded.getvalue(), content)

            read_url = self.adapter.generate_read_url(
                "smoke/local-object.bin", 60
            )
            read_response = requests.get(read_url, timeout=10)
        self.assertEqual(read_response.status_code, 200)
        self.assertEqual(read_response.content, content)

        captured_output = captured_stdout.getvalue() + captured_stderr.getvalue()
        self.assertNotIn(target.url, captured_output)
        self.assertNotIn(read_url, captured_output)
        self.assertNotIn("X-Amz-", captured_output)


if __name__ == "__main__":
    unittest.main()
