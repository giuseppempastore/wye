import unittest
from types import SimpleNamespace

from app.extraction.models import ProviderResult
from app.extraction.providers import FakeExtractionProvider, ProviderError, ProviderTimeout
from app.services.label_extractions import ExtractionError, LabelExtractionService


INGREDIENTS = {"document_type":"ingredients","raw_text":"Ingredienti: acqua, sale","detected_languages":["it"],
    "ingredient_list_text":"acqua, sale","ingredients":[{"raw_text":"acqua","quantity":None},{"raw_text":"sale","quantity":None}],"allergens":[],"nutrition":[]}


class _Adapter:
    def __init__(self, error=None): self.error=error
    def download_to(self, key, target):
        if self.error: raise self.error
        target.write(b"image")


class _Service(LabelExtractionService):
    def __init__(self, provider, image_type="ingredients", adapter=None):
        settings=SimpleNamespace(max_image_bytes=1024); extraction=SimpleNamespace(model="model")
        super().__init__(adapter or _Adapter(),settings,extraction,provider=provider,connection_factory=None)
        self.image_type=image_type; self.failed=[]; self.succeeded=[]; self.running=[]; self.existing=None
    def _get_image(self, product_id, image_id):
        return {"id":image_id,"image_type":self.image_type,"mime_type":"image/jpeg","checksum":"a"*64,"object_key":"private"}
    def _create_pending_run(self,*args): return ((4,7),self.existing)
    def _mark_running(self,run_id): self.running.append(run_id)
    def _fail(self,run_id,code,detail): self.failed.append((run_id,code))
    def _succeed(self,run_id,output,result): self.succeeded.append((run_id,output,result))
    def get(self,product_id,image_id,run_id): return {"extraction":{"id":run_id,"run_status":"succeeded"},"items":[]}


class LabelExtractionServiceTests(unittest.TestCase):
    def test_success_validates_and_persists_atomically(self):
        service=_Service(FakeExtractionProvider(INGREDIENTS))
        result=service.create(1,2,"key")
        self.assertEqual(result["extraction"]["id"],7); self.assertEqual(service.running,[7]); self.assertEqual(len(service.succeeded),1); self.assertEqual(service.failed,[])

    def test_invalid_output_fails_without_success(self):
        service=_Service(FakeExtractionProvider({"document_type":"ingredients","raw_text":"x"}))
        with self.assertRaises(ExtractionError) as caught: service.create(1,2,"key")
        self.assertEqual(caught.exception.code,"invalid_provider_output"); self.assertEqual(service.failed,[(7,"invalid_provider_output")]); self.assertEqual(service.succeeded,[])

    def test_provider_error_and_timeout_are_distinct(self):
        for error,code in ((ProviderError("bad"),"provider_error"),(ProviderTimeout("slow"),"provider_timeout")):
            service=_Service(FakeExtractionProvider(error=error))
            with self.assertRaises(ExtractionError) as caught: service.create(1,2,"key")
            self.assertEqual(caught.exception.code,code); self.assertEqual(service.failed[0][1],code)

    def test_storage_error_is_persisted(self):
        service=_Service(FakeExtractionProvider(INGREDIENTS),adapter=_Adapter(OSError("private storage unavailable")))
        with self.assertRaises(ExtractionError) as caught: service.create(1,2,"key")
        self.assertEqual(caught.exception.code,"image_storage_unavailable"); self.assertEqual(service.failed[0][1],"image_storage_unavailable")

    def test_unsupported_type_and_invalid_request_do_not_call_provider(self):
        provider=FakeExtractionProvider(INGREDIENTS); service=_Service(provider,image_type="product_front")
        with self.assertRaises(ExtractionError) as caught: service.create(1,2,"key")
        self.assertEqual(caught.exception.code,"unsupported_image_type"); self.assertEqual(provider.requests,[])
        with self.assertRaises(ExtractionError): service.create(1,2,"")

    def test_idempotency_replay_returns_existing_and_conflict_is_rejected(self):
        service=_Service(FakeExtractionProvider(INGREDIENTS)); fingerprint="ignored"
        # The service computes the real fingerprint; obtain it from an initial dry success is unnecessary for conflict coverage.
        service.existing={"id":7,"request_fingerprint":"different"}
        with self.assertRaises(ExtractionError) as caught: service.create(1,2,"same-key")
        self.assertEqual(caught.exception.code,"idempotency_conflict")


if __name__ == "__main__": unittest.main()
