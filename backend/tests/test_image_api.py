import os, unittest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routes.product_images import router

class ImageApiContractTests(unittest.TestCase):
    def setUp(self): self.client=TestClient(FastAPI()); self.client.app.include_router(router)
    def tearDown(self): os.environ.pop("WYE_IMAGE_API_KEY",None)
    def test_api_is_disabled_without_server_key_and_rejects_wrong_key(self):
        payload={"image_type":"product_front","mime_type":"image/jpeg","byte_size":10,"sha256":"a"*64}
        self.assertEqual(self.client.post("/products/1/images/uploads",json=payload).status_code,503)
        os.environ["WYE_IMAGE_API_KEY"]="secret"
        self.assertEqual(self.client.post("/products/1/images/uploads",json=payload,headers={"X-Wye-Image-Key":"wrong"}).status_code,401)
    def test_initialize_endpoint_contract(self):
        os.environ["WYE_IMAGE_API_KEY"]="secret"; service=Mock(); service.initialize.return_value={"upload_id":"u","upload_url":"https://private","method":"PUT","headers":{},"expires_at":"soon"}
        payload={"image_type":"product_front","mime_type":"image/jpeg","byte_size":10,"sha256":"a"*64}
        with patch("app.routes.product_images._service",return_value=service): response=self.client.post("/products/7/images/uploads",json=payload,headers={"X-Wye-Image-Key":"secret"})
        self.assertEqual(response.status_code,201); service.initialize.assert_called_once_with(7,"product_front","image/jpeg",10,"a"*64)
