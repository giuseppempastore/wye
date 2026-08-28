import os, unittest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.label_extractions import router
from app.services.label_extractions import ExtractionError


class LabelExtractionApiTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI(); app.include_router(router); self.client = TestClient(app)
    def tearDown(self): os.environ.pop("WYE_IMAGE_API_KEY", None)

    def test_temporary_auth_is_required(self):
        response = self.client.post("/products/1/images/2/extractions", json={}, headers={"Idempotency-Key":"k"})
        self.assertEqual(response.status_code, 503)

    def test_post_requires_and_forwards_idempotency_key(self):
        os.environ["WYE_IMAGE_API_KEY"] = "secret"; service = Mock(); service.create.return_value={"extraction":{"id":3},"items":[]}
        with patch("app.routes.label_extractions._service", return_value=service):
            response=self.client.post("/products/1/images/2/extractions",json={},headers={"X-Wye-Image-Key":"secret","Idempotency-Key":"retry-1"})
        self.assertEqual(response.status_code,201); service.create.assert_called_once_with(1,2,"retry-1",None,"label_extraction_v1")

    def test_stable_application_error_is_exposed(self):
        os.environ["WYE_IMAGE_API_KEY"]="secret"; service=Mock(); service.create.side_effect=ExtractionError("unsupported_image_type","Only ingredients and nutrition images are supported",422)
        with patch("app.routes.label_extractions._service",return_value=service):
            response=self.client.post("/products/1/images/2/extractions",json={},headers={"X-Wye-Image-Key":"secret","Idempotency-Key":"k"})
        self.assertEqual(response.status_code,422); self.assertEqual(response.json()["detail"]["code"],"unsupported_image_type")


if __name__ == "__main__": unittest.main()
