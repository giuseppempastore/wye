import os
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.ingredient_mapping_reviews import router
from app.services.ingredient_mapping_reviews import IngredientMappingReviewError


class IngredientMappingReviewApiTests(unittest.TestCase):
    def setUp(self):
        os.environ["WYE_IMAGE_API_KEY"] = "secret"
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)
        self.headers = {"X-Wye-Image-Key": "secret"}
        self.detail = {
            "review": {
                "review_id": 7,
                "review_status": "pending",
                "requested_by_method": "deterministic",
                "review_provenance": {},
                "created_at": datetime.now(timezone.utc),
                "reviewed_at": None,
                "reviewed_by": None,
            },
            "product_ingredient": {
                "id": 4,
                "product_id": 3,
                "raw_name": "E330",
                "normalized_text": "e330",
                "detected_language": "it",
                "position_in_list": 1,
                "mapping_status": "needs_review",
                "ingredient_id": None,
                "extracted_quantity": None,
            },
            "candidates": [{
                "candidate_id": 11,
                "ingredient_id": 13,
                "canonical_name": "Acido citrico",
                "candidate_method": "deterministic",
                "candidate_confidence": 1.0,
                "rationale": "exact alias",
                "is_selected": False,
            }],
        }

    def tearDown(self):
        os.environ.pop("WYE_IMAGE_API_KEY", None)

    def test_get_pending(self):
        service = Mock()
        service.list.return_value = {"reviews": [{
            "review_id": 7, "product_ingredient_id": 4, "product_id": 3,
            "raw_text": "E330", "normalized_text": "e330",
            "detected_language": "it", "review_status": "pending",
            "created_at": datetime.now(timezone.utc), "candidate_count": 1,
        }]}
        with patch("app.routes.ingredient_mapping_reviews._service", return_value=service):
            response = self.client.get("/ingredient-mapping-reviews?status=pending", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        service.list.assert_called_once_with("pending")

    def test_get_detail(self):
        service = Mock(); service.detail.return_value = self.detail
        with patch("app.routes.ingredient_mapping_reviews._service", return_value=service):
            response = self.client.get("/ingredient-mapping-reviews/7", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["candidates"][0]["canonical_name"], "Acido citrico")

    def test_review_not_found(self):
        service = Mock(); service.detail.side_effect = IngredientMappingReviewError("review_not_found", "not found", 404)
        with patch("app.routes.ingredient_mapping_reviews._service", return_value=service):
            response = self.client.get("/ingredient-mapping-reviews/99", headers=self.headers)
        self.assertEqual(response.status_code, 404)

    def test_accept_valid(self):
        service = Mock(); service.decide.return_value = self.detail
        with patch("app.routes.ingredient_mapping_reviews._service", return_value=service):
            response = self.client.post("/ingredient-mapping-reviews/7/decision", headers=self.headers, json={"status": "accepted", "candidate_id": 11})
        self.assertEqual(response.status_code, 200)
        service.decide.assert_called_once_with(7, "accepted", 11)

    def test_accept_without_candidate_is_422(self):
        response = self.client.post("/ingredient-mapping-reviews/7/decision", headers=self.headers, json={"status": "accepted"})
        self.assertEqual(response.status_code, 422)

    def test_ambiguous_and_rejected(self):
        for decision in ("ambiguous", "rejected"):
            service = Mock(); service.decide.return_value = self.detail
            with patch("app.routes.ingredient_mapping_reviews._service", return_value=service):
                response = self.client.post("/ingredient-mapping-reviews/7/decision", headers=self.headers, json={"status": decision})
            self.assertEqual(response.status_code, 200)
            service.decide.assert_called_once_with(7, decision, None)

    def test_terminal_review_is_409(self):
        service = Mock(); service.decide.side_effect = IngredientMappingReviewError("review_already_decided", "terminal", 409)
        with patch("app.routes.ingredient_mapping_reviews._service", return_value=service):
            response = self.client.post("/ingredient-mapping-reviews/7/decision", headers=self.headers, json={"status": "rejected"})
        self.assertEqual(response.status_code, 409)

    def test_wrong_candidate_is_404(self):
        service = Mock(); service.decide.side_effect = IngredientMappingReviewError("candidate_not_found", "wrong review", 404)
        with patch("app.routes.ingredient_mapping_reviews._service", return_value=service):
            response = self.client.post("/ingredient-mapping-reviews/7/decision", headers=self.headers, json={"status": "accepted", "candidate_id": 99})
        self.assertEqual(response.status_code, 404)

    def test_invalid_payloads_are_422(self):
        payloads = ({"status": "unknown"}, {"status": "ambiguous", "candidate_id": 11})
        for payload in payloads:
            response = self.client.post("/ingredient-mapping-reviews/7/decision", headers=self.headers, json=payload)
            self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
