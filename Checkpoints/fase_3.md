# WYE — Fase 3: Object Storage e acquisizione immagini

## Stato

**COMPLETATA E VALIDATA END-TO-END**

Branch:

```text
ingredients_score
```

Commit iniziale:

```text
b2f7391287ff671a24029d03b30660b9c5b6e444
```

Commit finale:

```text
non creato
```

Database di test finale:

```text
0004_product_image_uploads (head)
```

La Fase 3 ha introdotto il primo flusso applicativo completo di WYE per acquisire, verificare, versionare e rendere accessibili immagini prodotto.

---

## 1. Obiettivo della fase

La Fase 3 costruisce sopra le fondamenta delle Fasi 2 e 2.1 il flusso:

```text
client
  ↓
inizializzazione upload
  ↓
signed PUT
  ↓
staging object
  ↓
verifica backend
  ↓
SHA-256
  ↓
oggetto definitivo content-addressed
  ↓
storage_objects
  ↓
product_images
  ↓
supersession/versioning
  ↓
signed GET
```

Il contenuto binario delle immagini continua a non essere salvato in PostgreSQL.

---

## 2. File creati

```text
backend/migrations/versions/0004_product_image_uploads.py
backend/.env.example
backend/requirements-dev.txt
backend/app/security.py
backend/app/services/image_uploads.py
backend/app/storage/base.py
backend/app/storage/config.py
backend/app/storage/s3.py
backend/app/storage/__init__.py
backend/app/routes/product_images.py
backend/app/routes/__init__.py
backend/scripts/cleanup_image_uploads.py
backend/tests/test_image_api.py
backend/tests/test_image_uploads.py
backend/tests/test_image_upload_cleanup.py
backend/tests/test_s3_storage_integration.py
```

## 3. File modificati

```text
backend/app/main.py
backend/requirements.txt
backend/tests/test_data_integrity_hardening.py
```

Non sono stati modificati frontend, README e migration `0001`, `0002`, `0003`.

---

## 4. Migration `0004`

La migration crea:

```text
product_image_uploads
```

per tracciare il ciclo di vita temporaneo di un upload.

Stati:

```text
initiated
verifying
finalized
failed
abandoned
```

La tabella conserva:

- UUID upload;
- prodotto e tipo immagine;
- staging object identity;
- MIME, dimensione e SHA-256 dichiarati;
- metadata verificati;
- riferimenti finali a `storage_objects` e `product_images`;
- failure provenance;
- scadenze e timestamp.

Sono presenti constraint di coerenza, unicità dello staging object e indici per prodotto/tipo/stato/cleanup.

---

## 5. Upgrade, downgrade e re-upgrade

Verificati realmente:

```text
0003 → 0004    OK
0004 → 0003    OK su dati compatibili
0003 → 0004    OK
```

Il downgrade viene bloccato quando esistono audit record che andrebbero persi.

Database finale:

```text
0004_product_image_uploads (head)
```

---

## 6. StorageAdapter

Architettura:

```text
FastAPI
  ↓
ImageUploadService
  ↓
StorageAdapter
  ↓
S3StorageAdapter / boto3
```

Il codice applicativo non dipende direttamente da Boto3.

Provider previsti:

```text
Produzione consigliata → Cloudflare R2
Sviluppo locale       → MinIO
Test automatici       → Moto S3
Compatibile anche     → Amazon S3
```

---

## 7. Sicurezza storage

Gli oggetti sono privati.

Non vengono persistiti:

```text
signed URLs
temporary URLs
access tokens
credentials
```

Il client riceve signed PUT solo sulla staging key, mai sulla key definitiva.

---

## 8. Flusso upload

```text
1. initialize
2. verifica chiave API e prodotto
3. creazione product_image_uploads
4. staging key casuale
5. signed PUT
6. upload diretto
7. finalize
8. HEAD
9. download streaming
10. verifica MIME/magic bytes
11. verifica dimensione
12. ricalcolo SHA-256
13. promozione su key finale
14. create/reuse storage_objects
15. creazione product_images
16. supersession immagine precedente
17. upload → finalized
18. cleanup staging best-effort
```

---

## 9. Endpoint

```text
POST /products/{product_id}/images/uploads
POST /products/{product_id}/images/uploads/{upload_id}/finalize
GET  /products/{product_id}/images
GET  /products/{product_id}/images/{image_id}/access
```

Protezione temporanea:

```text
X-Wye-Image-Key
```

---

## 10. Sicurezza API temporanea

Configurazione:

```text
WYE_IMAGE_API_KEY
```

Comportamento:

```text
server senza chiave configurata → 503
chiave mancante                 → 401
chiave errata                   → 401
chiave valida                   → accesso
```

Questa non è l'autenticazione definitiva di WYE. Mancano ancora JWT/sessioni/ownership/autorizzazione per prodotto.

---

## 11. Policy immagini

MIME ammessi:

```text
image/jpeg
image/png
image/webp
```

Limite predefinito:

```text
15 MiB
```

Controlli magic bytes:

```text
JPEG → FF D8 FF
PNG  → firma PNG
WebP → RIFF....WEBP
```

Il filename originale del client viene ignorato.

---

## 12. Checksum

Per i nuovi upload:

```text
SHA-256
```

Il backend ricalcola realmente il checksum dallo stream.

Mismatch:

```text
upload → failed
```

L'oggetto finale usa una key content-addressed:

```text
objects/sha256/{prefix}/{sha256}
```

---

## 13. Streaming

La verifica usa:

```text
SpooledTemporaryFile
```

Il file non viene salvato in PostgreSQL e non deve necessariamente restare interamente in RAM.

---

## 14. Deduplicazione

Blob identici possono riutilizzare lo stesso:

```text
storage_object
```

pur appartenendo a diversi:

```text
product_images
```

---

## 15. Idempotenza

Una seconda `finalize` sullo stesso upload restituisce lo stesso risultato logico:

```text
storage_object_id
product_image_id
```

senza creare duplicati.

---

## 16. Concorrenza e supersession

Il servizio serializza le sostituzioni tramite lock PostgreSQL sul prodotto.

La vecchia immagine diventa:

```text
superseded
```

La nuova:

```text
active/current
```

È stato eseguito un test concorrente reale: lo stato finale mantiene una sola immagine `current`.

---

## 17. Signed URLs

Upload URL predefinita:

```text
15 minuti
```

Read URL predefinita:

```text
5 minuti
```

Le URL non vengono persistite.

---

## 18. Upload orfani

Script:

```text
backend/scripts/cleanup_image_uploads.py
```

Gestisce upload scaduti `initiated`/`verifying` tramite:

```text
FOR UPDATE SKIP LOCKED
```

Li marca `abandoned` e rimuove solo lo staging object best-effort.

Non elimina oggetti definitivi o immagini finalizzate.

Non è stato introdotto uno scheduler automatico.

---

## 19. Product label documents

La Fase 3 non crea automaticamente:

```text
product_label_documents
```

La fase termina intenzionalmente a:

```text
storage_objects
→ product_images
```

La creazione dei documenti verrà affrontata nella pipeline OCR/AI.

---

## 20. Configurazione

```text
WYE_IMAGE_API_KEY
WYE_STORAGE_PROVIDER
WYE_STORAGE_ENDPOINT
WYE_STORAGE_BUCKET
WYE_STORAGE_REGION
WYE_STORAGE_ACCESS_KEY
WYE_STORAGE_SECRET_KEY
WYE_STORAGE_FORCE_PATH_STYLE
WYE_STORAGE_UPLOAD_TTL_SECONDS
WYE_STORAGE_READ_TTL_SECONDS
WYE_STORAGE_MAX_IMAGE_BYTES
WYE_STORAGE_CLEANUP_AFTER_SECONDS
```

Nessun secret reale è stato inserito.

---

## 21. Test Fase 3

```text
8 eseguiti
8 passed
0 failed
0 errors
0 skipped
```

Coprono API, signed PUT/GET, staging, verifica contenuto, SHA-256, storage objects, product images, idempotenza, supersession, concorrenza, cleanup ed E2E Moto S3.

Suite completa:

```text
34 eseguiti
32 passed
0 failed
2 errors
0 skipped
```

I due errori sono preesistenti:

```text
Client.__init__() got an unexpected keyword argument 'proxies'
```

relativi a OpenAI/httpx.

---

## 22. Provider reale

La compatibilità S3 è stata verificata tramite Moto.

Non sono ancora stati verificati contro account reali:

```text
Cloudflare R2
Amazon S3
MinIO
```

---

## 23. Problema repository individuato

Git traccia accidentalmente circa:

```text
4034 file sotto backend/venv
1859 file sotto __pycache__
```

Manca inoltre un `.gitignore` adeguato.

Durante la Fase 3 non sono state fatte operazioni invasive di untracking.

È consigliata una breve **Fase 3.1 — Repository Hygiene** prima della Fase 4.

---

## 24. Rischi residui

- manca autenticazione/ownership reale;
- R2/AWS/MinIO non sono ancora testati su account reali;
- cleanup non schedulato;
- incompatibilità OpenAI/httpx ancora aperta;
- `venv` e `__pycache__` ancora tracciati da Git.

---

## 25. Stato finale

```text
Migration 0004              ✅
StorageAdapter              ✅
Signed PUT                  ✅
Staging                     ✅
Verifica contenuto          ✅
SHA-256                     ✅
Final object                ✅
storage_objects             ✅
product_images              ✅
Idempotenza                 ✅
Supersession                ✅
Concorrenza                 ✅
Signed GET                  ✅
Cleanup orfani              ✅
Upgrade/downgrade           ✅
Test Fase 3                 ✅ 8/8
```

# ✅ FASE 3 COMPLETATA

---

## 26. Roadmap aggiornata

```text
Fase 1      ✅ Alembic e baseline
Fase 2      ✅ Modello scientifico e provenance
Fase 2.1    ✅ Data Integrity Hardening
Fase 3      ✅ Object Storage e acquisizione immagini
Fase 3.1    ⏳ Repository Hygiene
Fase 4      ⏳ OCR / AI / parsing etichetta
Fase 5      ⏳ Normalizzazione e review mapping
Fase 6      ⏳ EFSA / OpenFoodTox ingestion
Fase 7      ⏳ Scoring scientifico versionato
```

### Sintesi semplice

WYE ora sa acquisire un'immagine in modo sicuro, verificarla, identificarla tramite SHA-256, conservarne la provenance, collegarla a un prodotto, versionarla e fornire accesso temporaneo controllato.

Non interpreta ancora il contenuto dell'immagine. Questo sarà il compito della futura Fase 4.
