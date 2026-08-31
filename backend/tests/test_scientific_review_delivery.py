import json
from pathlib import Path
import shutil
import tempfile
import unittest

from app.scientific_evaluation.review_delivery import (
    DELIVERY_CONTENT_DIGEST,
    DELIVERY_MANIFEST_DIGEST,
    DELIVERY_PACKAGE_RELATIVE_PATH,
    ReviewDeliveryIntegrityError,
    validate_review_delivery,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PACKAGE = REPOSITORY_ROOT / DELIVERY_PACKAGE_RELATIVE_PATH


class ScientificReviewDeliveryTests(unittest.TestCase):
    def _copy_package(self, temporary_root: Path) -> Path:
        destination = temporary_root / "delivery"
        shutil.copytree(SOURCE_PACKAGE, destination)
        return destination

    def _assert_invalid(self, package: Path, pattern: str | None = None) -> None:
        context = self.assertRaises(ReviewDeliveryIntegrityError)
        with context:
            validate_review_delivery(REPOSITORY_ROOT, package)
        if pattern is not None:
            self.assertIn(pattern, str(context.exception))

    def test_pristine_delivery_validates(self):
        result = validate_review_delivery(REPOSITORY_ROOT)

        self.assertEqual(result.file_count, 8)
        self.assertEqual(result.manifest_digest, DELIVERY_MANIFEST_DIGEST)
        self.assertEqual(result.package_content_digest, DELIVERY_CONTENT_DIGEST)
        self.assertEqual(result.candidate_version, "1.0.0-candidate.1")
        self.assertEqual(
            result.candidate_digest,
            "d5c98f988ae1ef8514518a97cbc00d1f5c6d5984ae7fea7a60c7c113dc833615",
        )
        self.assertEqual(
            result.golden_corpus_digest,
            "db535148ece59c222eaac2004594ae19a1e00a2e65448c42a4804dd8cefd8b15",
        )

    def test_missing_required_file_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._copy_package(Path(temporary))
            (package / "WYE_SELECTION_POLICY_EXTERNAL_REVIEW_HANDOFF.md").unlink()

            self._assert_invalid(package, "closed-set mismatch")

    def test_modified_frozen_candidate_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._copy_package(Path(temporary))
            candidate = package / "WYE_SELECTION_POLICY_CANDIDATE_V1.json"
            candidate.write_bytes(candidate.read_bytes() + b" ")

            self._assert_invalid(package, "file size or digest mismatch")

    def test_modified_golden_corpus_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._copy_package(Path(temporary))
            corpus = package / "WYE_SELECTION_GOLDEN_CASES.md"
            corpus.write_bytes(corpus.read_bytes() + b"\nchanged")

            self._assert_invalid(package, "frozen review subject is invalid")

    def test_modified_supporting_file_with_manifest_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._copy_package(Path(temporary))
            supporting = package / "WYE_SELECTION_POLICY_FREEZE.md"
            supporting.write_bytes(supporting.read_bytes() + b"\nchanged")

            self._assert_invalid(package, "file size or digest mismatch")

    def test_manifest_digest_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._copy_package(Path(temporary))
            path = package / "DELIVERY_MANIFEST.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["package_content_digest"] = "0" * 64
            path.write_text(json.dumps(manifest), encoding="utf-8")

            self._assert_invalid(package, "manifest digest mismatch")

    def test_unexpected_file_fails_closed_set(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._copy_package(Path(temporary))
            (package / "UNEXPECTED.txt").write_text("unexpected", encoding="utf-8")

            self._assert_invalid(package, "closed-set mismatch")

    def test_wrong_candidate_version_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._copy_package(Path(temporary))
            path = package / "WYE_SELECTION_POLICY_CANDIDATE_V1.json"
            candidate = json.loads(path.read_text(encoding="utf-8"))
            candidate["policy_version"] = "1.0.0-candidate.2"
            path.write_text(json.dumps(candidate), encoding="utf-8")

            self._assert_invalid(package, "candidate policy_version changed")

    def test_wrong_candidate_digest_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._copy_package(Path(temporary))
            path = package / "WYE_SELECTION_POLICY_CANDIDATE_V1.json"
            content = path.read_text(encoding="utf-8")
            path.write_text(
                content.replace(
                    '"target_type": "substance"',
                    '"target_type": "substancf"',
                    1,
                ),
                encoding="utf-8",
            )

            self._assert_invalid(package, "candidate canonical digest changed")

    def test_wrong_golden_corpus_digest_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = self._copy_package(Path(temporary))
            path = package / "WYE_SELECTION_GOLDEN_CORPUS_MANIFEST.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["case_count"] = 27
            path.write_text(json.dumps(manifest), encoding="utf-8")

            self._assert_invalid(package, "golden corpus digest changed")


if __name__ == "__main__":
    unittest.main()
