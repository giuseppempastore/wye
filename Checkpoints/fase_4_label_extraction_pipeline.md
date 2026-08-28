# WYE — Fase 4: Label Extraction Pipeline

## Stato

**COMPLETATA E VALIDATA**

Branch:

```text
ingredients_score
```

Commit di partenza:

```text
1f767b14603d1e20e9c80b7cb7dd980fc622839b
```

Commit finale:

```text
non ancora creato
```

La Fase 4 ha introdotto la pipeline completa per interpretare immagini di etichette già acquisite dalla Fase 3 e trasformarle in dati strutturati, mantenendo separata l'estrazione dalla futura normalizzazione scientifica.

> Nota residua: Codex ha rilevato che la repository sembrerebbe ancora tracciare 4.052 artefatti storici sotto `backend/venv` / `__pycache__`, in contrasto con il documento della Fase 3.1. Questa anomalia deve essere verificata separatamente prima del commit finale, ma non risulta introdotta dalla Fase 4.

---

## 1. Obiettivo della fase

La Fase 4 implementa il flusso:

```text
product_images
      ↓
storage_objects
      ↓
StorageAdapter
      ↓
download privato immagine
      ↓
product_label_documents
      ↓
label_extraction_runs
      ↓
ExtractionProvider
      ↓
validazione Pydantic
      ↓
label_extraction_items
```

La Fase 4 risponde quindi alla domanda:

```text
"Cosa c'è scritto sull'etichetta?"
```

Non risponde ancora a:

```text
"Qual è l'ingrediente canonico WYE?"
"Quali evidenze scientifiche esistono?"
"Qual è lo score del prodotto?"
```

Questi compiti restano nelle fasi successive.

---

## 2. Scope rispettato

La Fase 4 NON introduce:

- normalizzazione degli ingredienti;
- scritture in `ingredients`;
- scritture in `ingredient_aliases`;
- scritture in `product_ingredients`;
- mapping scientifici;
- EFSA / OpenFoodTox;
- scoring;
- traduzione automatica degli ingredienti;
- modifiche al frontend Flutter.

Nei nuovi moduli non risultano riferimenti a:

```text
normalize_ingredient
ingredients
ingredient_aliases
product_ingredients
scientific_assessments
product_scores
score_product
EFSA
OpenFoodTox
```

La separazione tra estrazione e interpretazione scientifica è quindi mantenuta.

---

## 3. File creati

### Extraction layer

```text
backend/app/extraction/models.py
backend/app/extraction/config.py
backend/app/extraction/providers/base.py
backend/app/extraction/providers/openai.py
backend/app/extraction/providers/fake.py
backend/app/extraction/prompts/label_extraction_v1.py
```

### Service e API

```text
backend/app/services/label_extractions.py
backend/app/routes/label_extractions.py
```

### Database

```text
backend/migrations/versions/0005_label_extraction_pipeline.py
```

### Test

```text
backend/tests/test_extraction_providers.py
backend/tests/test_label_extraction_api.py
backend/tests/test_label_extraction_migration.py
backend/tests/test_label_extraction_models.py
backend/tests/test_label_extraction_service.py
```

---

## 4. File modificati

```text
backend/app/main.py
backend/requirements.txt
backend/.env.example
```

Modifiche principali:

- registrazione del nuovo router FastAPI;
- aggiornamento delle dipendenze OpenAI / HTTPX;
- aggiunta della configurazione extraction.

Nessuna migration precedente (`0001–0004`) è stata modificata.

---

## 5. Migration `0005`

Migration introdotta:

```text
0005_label_extraction_pipeline
```

Nuovo head Alembic:

```text
0005_label_extraction_pipeline
```

La migration estende il modello già creato nelle Fasi 2 e 2.1.

### `product_label_documents`

Aggiunge:

```text
document_type
```

e consente al documento di esistere prima che il testo sia stato estratto.

Per questo:

```text
raw_text
```

può essere temporaneamente `NULL`.

È inoltre introdotta una policy coerente tra:

```text
product_image.image_type
product_label_document.document_type
```

In particolare:

```text
ingredients → ingredients
nutrition   → nutrition
```

Un trigger PostgreSQL impedisce mismatch tra i due tipi.

È presente inoltre l'unicità del documento logico per immagine/tipo.

---

## 6. Lifecycle delle estrazioni

Gli stati supportati sono:

```text
pending
running
succeeded
failed
superseded
```

I vecchi record:

```text
completed
```

vengono convertiti a:

```text
succeeded
```

La pipeline principale è:

```text
document create/reuse
        ↓
pending
        ↓
running
        ↓
download immagine
        ↓
provider AI
        ↓
validazione Pydantic
        ↓
scrittura atomica items
        ↓
succeeded
```

In caso di errore:

```text
failed
+ error_code
+ error_detail sanitizzato
+ zero item parziali
```

---

## 7. Provenance del run

`label_extraction_runs` conserva informazioni necessarie per rendere ogni estrazione tracciabile.

Sono stati aggiunti o gestiti:

```text
extracted_raw_text
error_code
error_detail
provider_request_id
schema_version
prompt_hash
idempotency_key
request_fingerprint
started_at
completed_at
```

In questo modo due esecuzioni differenti sulla stessa immagine restano distinguibili.

---

## 8. Architettura provider-neutral

Il service layer dipende da un contratto astratto:

```text
ExtractionProvider.extract(request)
        ↓
ProviderResult
```

Implementazioni introdotte:

```text
OpenAIExtractionProvider
FakeExtractionProvider
```

Non è stato introdotto Gemini in questa fase.

Il vantaggio è che la pipeline applicativa non dipende direttamente da OpenAI:

```text
LabelExtractionService
        ↓
ExtractionProvider
        ↓
OpenAI / Fake / provider futuro
```

---

## 9. Fake provider

È stato introdotto:

```text
FakeExtractionProvider
```

Serve a eseguire test deterministici senza:

- connessione Internet;
- API key reale;
- chiamate OpenAI;
- costi;
- dipendenza dalla disponibilità del provider.

La suite standard della Fase 4 utilizza quindi test offline.

---

## 10. OpenAI

La vecchia configurazione presentava due incompatibilità:

```text
openai==1.40.3
httpx==0.28.1
```

Problemi:

```text
Client.__init__() got an unexpected keyword argument 'proxies'
```

e assenza di:

```text
client.responses
```

La Fase 4 utilizza ora:

```text
openai==1.109.1
httpx==0.28.1
```

Le versioni sono state verificate in un virtualenv pulito con:

```text
Python 3.11.5
OpenAI 1.109.1
HTTPX 0.28.1
client.responses disponibile: True
```

È stata mantenuta la major 1 dell'SDK per ridurre la superficie di migrazione.

---

## 11. OpenAI Responses API

`OpenAIExtractionProvider` utilizza:

```text
Responses API
```

con:

- input immagine;
- Structured Outputs;
- schema strict;
- `store=False`.

L'immagine viene trasformata in una data URL solamente in memoria per la richiesta al provider.

La rappresentazione base64 non viene persistita nel database.

---

## 12. Accesso privato all'immagine

Il provider AI non riceve signed URL dello storage.

Il percorso implementato è:

```text
product_images
      ↓
storage_objects
      ↓
StorageAdapter.download_to()
      ↓
SpooledTemporaryFile
      ↓
bytes
      ↓
ExtractionProvider
```

Questo mantiene gli oggetti storage privati.

Non vengono persistiti:

```text
signed URLs
base64 immagini
access token
credenziali
```

Resta valido il limite immagini introdotto nella Fase 3:

```text
15 MiB
```

---

## 13. Tipi immagine supportati

In questa prima versione:

```text
ingredients     ✅
nutrition       ✅
product_front   ❌
other           ❌
```

Per tipi non supportati l'API restituisce:

```text
HTTP 422
unsupported_image_type
```

Il sistema non tenta quindi di indovinare il contenuto di immagini non previste.

---

## 14. Prompt versionato

È stato creato:

```text
label_extraction_v1
```

Il prompt e lo schema sono versionati.

Il run conserva inoltre:

```text
schema_version
prompt_hash
```

Questo rende possibile sapere quale versione della logica di estrazione ha prodotto un determinato risultato.

---

## 15. Principi di estrazione

Il provider è configurato per:

- trascrivere ciò che osserva;
- preservare il testo originale;
- non inventare dati mancanti;
- non tradurre automaticamente;
- non normalizzare gli ingredienti;
- non creare valori numerici assenti;
- utilizzare `null` o strutture vuote quando il dato non è disponibile.

La validazione Pydantic viene eseguita prima della persistenza del risultato positivo.

---

## 16. Estrazione ingredienti

Per immagini:

```text
image_type = ingredients
```

vengono gestiti:

- raw text completo;
- lingue rilevate;
- lista ingredienti;
- ingredienti nell'ordine osservato;
- allergeni espliciti;
- quantità visibili.

Persistenza concettuale:

```text
ingredient_list
ingredient
ingredient
ingredient
allergen
...
```

Non viene chiamato:

```text
normalize_ingredient
```

Il testo rimane quindi ancora vicino a ciò che è stato realmente letto dall'etichetta.

---

## 17. Estrazione nutrizionale

Per immagini:

```text
image_type = nutrition
```

viene creato un item per nutriente.

Lo `structured_value` può contenere:

```text
nutrient
raw_label
value
unit
basis
```

Nutrienti inizialmente supportati:

```text
energy
fat
saturated_fat
carbohydrate
sugars
protein
salt
fiber
```

La basis può rappresentare casi come:

```text
per 100 g
per 100 ml
per porzione
```

Se non è leggibile viene lasciata `NULL`.

Non viene inventata.

---

## 18. Atomicità

Regola:

```text
provider output valido
→ items completi
→ succeeded
```

oppure:

```text
provider output invalido
→ failed
→ zero items parziali
```

La scrittura degli item e il passaggio allo stato `succeeded` avvengono atomicamente.

Questo evita estrazioni parzialmente salvate come valide.

---

## 19. Idempotenza

Il POST richiede:

```text
Idempotency-Key
```

Il fingerprint comprende:

```text
checksum immagine
document type
provider
model
prompt version
schema version
```

Comportamento:

```text
stessa key + stesso fingerprint
→ stesso run

stessa key + fingerprint differente
→ HTTP 409

nuova key
→ nuovo run
```

La concorrenza è protetta anche tramite:

```text
ON CONFLICT
```

---

## 20. Endpoint

Sono stati introdotti:

```text
POST /products/{product_id}/images/{image_id}/extractions

GET /products/{product_id}/images/{image_id}/extractions

GET /products/{product_id}/images/{image_id}/extractions/{run_id}
```

La protezione temporanea continua a utilizzare:

```text
X-Wye-Image-Key
```

Questa protezione non rappresenta ancora autenticazione e ownership definitive.

---

## 21. Configurazione

Sono state aggiunte configurazioni esplicite:

```text
WYE_EXTRACTION_PROVIDER=openai
WYE_OPENAI_API_KEY=replace-me
WYE_OPENAI_EXTRACTION_MODEL=gpt-4o-mini
WYE_EXTRACTION_TIMEOUT_SECONDS=90
```

Il provider viene selezionato esplicitamente.

Non viene dedotto dal formato della API key.

---

## 22. Error handling

La pipeline distingue gli errori applicativi e salva informazioni diagnostiche controllate.

Tra i casi gestiti:

```text
unsupported image type
image not found
storage/image unavailable
invalid provider output
provider timeout
provider error
idempotency conflict
invalid request
```

Gli error detail vengono sanitizzati prima della persistenza/esposizione.

---

## 23. Test Fase 4

Test specifici Fase 4 senza rete:

```text
13 / 13 passed
```

Test migration PostgreSQL `0005`:

```text
2 / 2 passed
```

Nessuna chiamata reale OpenAI è stata effettuata.

---

## 24. Suite backend completa

Risultato:

```text
52 test rilevati
30 passed
22 skipped
0 failed
0 errors
```

I 22 test skipped sono test PostgreSQL opt-in.

I test PostgreSQL specifici della migration `0005` sono stati comunque eseguiti separatamente su database temporaneo isolato.

---

## 25. Validazione PostgreSQL reale

È stato utilizzato un database temporaneo isolato.

Percorso verificato:

```text
0001
↓
0002
↓
0003
↓
0004
↓
0005
```

Risultato:

```text
0001 → 0005     OK
0005 → 0004     OK
0004 → 0005     OK
```

Head finale:

```text
0005_label_extraction_pipeline
```

Il database temporaneo è stato eliminato al termine.

Il database storico locale:

```text
wye
```

non è stato modificato.

---

## 26. Git validation

Eseguito:

```text
git diff --check
```

Risultato:

```text
OK
```

Sono presenti soltanto warning relativi ai line ending CRLF di Windows.

`backend/tests/test_ai_normalizer.py` può apparire modificato nello status per metadati/line ending, ma il contenuto coincide con HEAD e non presenta un diff effettivo.

---

## 27. Rischi residui

### Provider AI reale

La pipeline è tecnicamente implementata, ma il provider deve ancora essere valutato su un corpus reale di immagini WYE.

Andranno testati casi come:

- inclinazione;
- riflessi;
- fotografie sfocate;
- lingue differenti;
- ingredienti annidati;
- tabelle nutrizionali complesse;
- testo parzialmente visibile.

### Modello

Il modello configurato inizialmente è:

```text
gpt-4o-mini
```

La scelta definitiva del modello dovrà essere effettuata dopo benchmark.

### Autenticazione

Continua a essere temporaneamente utilizzato:

```text
X-Wye-Image-Key
```

Mancano ancora autenticazione utente, ownership e autorizzazione reale per prodotto.

### Worker

La pipeline è sincrona.

Non sono stati introdotti:

```text
Celery
Redis
BackgroundTasks
```

come previsto.

L'architettura è predisposta per una futura esecuzione asincrona.

### Repository hygiene

Codex ha rilevato che circa:

```text
4.052
```

artefatti storici sotto:

```text
backend/venv
__pycache__
```

risulterebbero ancora tracciati.

Questa osservazione è in contrasto con la Fase 3.1, che li riportava come rimossi dal tracking Git.

La situazione deve essere verificata separatamente prima del commit finale.

Non risulta comunque essere stata introdotta dalla Fase 4.

---

## 28. Stato finale

```text
Migration 0005                  ✅
Document lifecycle              ✅
Extraction lifecycle            ✅
Provider abstraction            ✅
OpenAI provider                 ✅
Fake provider                   ✅
Responses API                   ✅
Structured Outputs              ✅
Prompt versioning               ✅
Pydantic validation             ✅
Ingredient extraction           ✅
Nutrition extraction            ✅
Atomic persistence              ✅
Idempotency                     ✅
Private storage access          ✅
API endpoints                   ✅
Error handling                  ✅
OpenAI/httpx compatibility      ✅
Test Fase 4                     ✅ 13/13
Migration test PostgreSQL       ✅ 2/2
Upgrade/downgrade/re-upgrade    ✅
No normalization                ✅
No EFSA                         ✅
No scoring                      ✅

Benchmark immagini reali        ⏳ futuro
Autenticazione definitiva       ⏳ futuro
Repository hygiene re-check     ⚠️ da verificare
Commit Git Fase 4               ⏳ da creare
```

# ✅ FASE 4 TECNICAMENTE COMPLETATA

---

## 29. Roadmap aggiornata

```text
Fase 1
Alembic e baseline
✅ COMPLETATA

Fase 2
Modello dati scientifico e provenance
✅ COMPLETATA

Fase 2.1
Data Integrity Hardening
✅ COMPLETATA

Fase 3
Object Storage e acquisizione immagini
✅ COMPLETATA

Fase 3.1
Repository Hygiene
✅ COMPLETATA
⚠️ stato tracking da riverificare

Fase 4
OCR / AI / parsing etichetta
✅ COMPLETATA

Fase 4.1
Benchmark provider / immagini reali / osservabilità
⏳ OPZIONALE PRIMA DELLA FASE 5

Fase 5
Normalizzazione e review mapping
⏳ PROSSIMA

Fase 6
EFSA / OpenFoodTox ingestion
⏳ PIANIFICATA

Fase 7
Scoring scientifico versionato
⏳ PIANIFICATA
```

---

## 30. Sintesi semplice

WYE ora è in grado di prendere una fotografia di una lista ingredienti o di una tabella nutrizionale già caricata nel proprio storage privato, inviarla a un provider AI attraverso un'architettura sostituibile, validare rigorosamente la risposta e salvare il contenuto estratto in forma strutturata e tracciabile.

Il sistema conserva:

```text
cosa è stato letto
da quale immagine
con quale provider
con quale modello
con quale prompt
con quale versione dello schema
in quale esecuzione
```

senza ancora decidere quale ingrediente canonico rappresenti il testo e senza attribuire valutazioni scientifiche.

Questa separazione prepara direttamente la prossima fase:

# Fase 5 — Normalizzazione e review mapping
