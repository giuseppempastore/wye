import json, unittest
from types import SimpleNamespace

from app.extraction.models import ExtractionRequest
from app.extraction.providers.fake import FakeExtractionProvider
from app.extraction.providers.openai import OpenAIExtractionProvider


def request():
    return ExtractionRequest(image_bytes=b"private-image", mime_type="image/jpeg", document_type="ingredients",
        model="test-model", prompt_version="label_extraction_v1", schema_version="1", instructions="extract",
        output_schema={"type": "object", "properties": {}})


class _Responses:
    def __init__(self): self.kwargs = None
    def create(self, **kwargs):
        self.kwargs = kwargs
        payload = {"document_type":"ingredients","raw_text":"water","ingredient_list_text":"water","ingredients":[{"raw_text":"water","quantity":None}],"allergens":[],"nutrition":[],"detected_languages":["en"]}
        return SimpleNamespace(id="resp_test", model="test-model", output_text=json.dumps(payload), model_dump=lambda **_: {"id":"resp_test"})


class ExtractionProviderTests(unittest.TestCase):
    def test_fake_records_request_without_network(self):
        provider = FakeExtractionProvider(output={"ok": True})
        result = provider.extract(request())
        self.assertEqual(result.output, {"ok": True}); self.assertEqual(len(provider.requests), 1)

    def test_openai_uses_responses_structured_output_and_private_data_url(self):
        responses = _Responses(); client = SimpleNamespace(responses=responses)
        result = OpenAIExtractionProvider("", client=client).extract(request())
        self.assertEqual(result.provider_request_id, "resp_test")
        content = responses.kwargs["input"][0]["content"]
        self.assertTrue(content[1]["image_url"].startswith("data:image/jpeg;base64,"))
        self.assertEqual(responses.kwargs["text"]["format"]["type"], "json_schema")
        self.assertFalse(responses.kwargs["store"])


if __name__ == "__main__": unittest.main()
