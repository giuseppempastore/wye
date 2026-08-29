import os
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.ingredient_mapping_reviews import router
from app.services.ingredient_mapping_reviews import IngredientMappingReviewError


class ReviewedAliasApprovalApiTests(unittest.TestCase):
    def setUp(self):
        app=FastAPI(); app.include_router(router); self.client=TestClient(app)
        self.alias={"alias":{"id":5,"ingredient_id":3,"alias_name":"E-330","normalized_alias":"e330","language":"it","alias_type":"synonym","confidence":1.0,"is_primary":False,"mapping_method":"manual_review","mapping_status":"accepted","approved_at":datetime.now(timezone.utc),"review_provenance":{},"created_at":datetime.now(timezone.utc)},"created":True}

    def tearDown(self):
        os.environ.pop("WYE_IMAGE_API_KEY",None)

    def authorized(self):
        os.environ["WYE_IMAGE_API_KEY"]="secret"
        return {"X-Wye-Image-Key":"secret"}

    def test_valid_approval_returns_200(self):
        service=Mock(); service.approve_alias.return_value=self.alias
        with patch("app.routes.ingredient_mapping_reviews._service",return_value=service):
            response=self.client.post("/ingredient-mapping-reviews/7/approve-alias",headers=self.authorized())
        self.assertEqual(response.status_code,200); self.assertTrue(response.json()["created"])
        service.approve_alias.assert_called_once_with(7)

    def test_missing_review_is_404(self):
        service=Mock(); service.approve_alias.side_effect=IngredientMappingReviewError("review_not_found","not found",404)
        with patch("app.routes.ingredient_mapping_reviews._service",return_value=service):
            response=self.client.post("/ingredient-mapping-reviews/99/approve-alias",headers=self.authorized())
        self.assertEqual(response.status_code,404)

    def test_nonaccepted_review_is_409(self):
        service=Mock(); service.approve_alias.side_effect=IngredientMappingReviewError("review_not_accepted","not accepted",409)
        with patch("app.routes.ingredient_mapping_reviews._service",return_value=service):
            response=self.client.post("/ingredient-mapping-reviews/7/approve-alias",headers=self.authorized())
        self.assertEqual(response.status_code,409)

    def test_collision_is_409(self):
        service=Mock(); service.approve_alias.side_effect=IngredientMappingReviewError("alias_collision","collision",409)
        with patch("app.routes.ingredient_mapping_reviews._service",return_value=service):
            response=self.client.post("/ingredient-mapping-reviews/7/approve-alias",headers=self.authorized())
        self.assertEqual(response.status_code,409)

    def test_repeated_request_returns_existing_alias(self):
        service=Mock(); existing=dict(self.alias); existing["created"]=False; service.approve_alias.return_value=existing
        with patch("app.routes.ingredient_mapping_reviews._service",return_value=service):
            response=self.client.post("/ingredient-mapping-reviews/7/approve-alias",headers=self.authorized())
        self.assertEqual(response.status_code,200); self.assertFalse(response.json()["created"])

    def test_temporary_api_key_is_required(self):
        response=self.client.post("/ingredient-mapping-reviews/7/approve-alias")
        self.assertEqual(response.status_code,503)


if __name__ == "__main__":
    unittest.main()
