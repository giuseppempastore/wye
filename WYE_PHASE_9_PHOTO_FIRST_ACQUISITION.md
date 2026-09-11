# WYE Phase 9.3A — Photo-first product acquisition

## Phase 9.3A.2 decisions

- Public registration and Premium instant analysis are separate paths.
- Public registration requires scanner-derived barcode plus `product_front`,
  `ingredients`, and `nutrition` documents.
- A versioned draft uses existing Hive storage and retains app-owned file paths,
  raw OCR/extraction and completed image IDs, never tokens, signed URLs,
  duplicate image bytes or provider payloads.
- Migration `0025_product_acquisition_jobs` persists acquisitions, document
  associations, bounded jobs and transition audit events.
- Docker `acquisition-worker` recovers expired leases and moves a submission
  through `queued -> processing -> extracted -> needs_review`.
- Admin validation exists in the status/audit contract; the full admin UI is
  deferred. Verified products remain read-only.
- `salt_g` means grams of salt and `sodium_mg` milligrams of sodium. No silent
  conversion or ambiguous `salt_mg` field is introduced.
- Premium is production-BLOCKED because the repository lacks production
  entitlement and the local DB has no published protocol/publication.

## Runtime slice implemented

The mobile acquisition path is now:

```text
validated product barcode
→ existing-product lookup or idempotent pending product creation
→ ingredients/nutrition photo and crop
→ on-device Google ML Kit Latin text recognition
→ explicit script classification and installed-script guard
→ abstract language detection (`und` when no result is reliable)
→ purpose-specific structural parser with versioned lexicons
→ optional backend-only text normalization fallback
→ canonical English candidates, validation and user review
→ user review of extracted values
→ persistence as unverified/pending review after Save
→ canonical non-numeric score-unavailable state
```

The barcode is the product identity. EAN-8, UPC-A, EAN-13 and GTIN-14 are
validated for numeric content, length and check digit. URL/QR text is rejected,
the full value is not logged, and a repeated create request returns the existing
record without overwriting it. A verified product is never silently overwritten;
the current mobile UI also blocks replacement image upload until an admin-review
proposal contract is implemented.

## Controlled manual fields

Name and brand remain user-editable text. Type and category use stable IDs and
localized Italian labels. The API accepts the same allowlists. Existing database
columns are reused; no duplicate classification columns were introduced.

Every newly created product is persisted with `verified=false`,
`status=needs_review`, and a pending `product_reviews` record. UI copy is
`Dati etichetta non verificati`. On-device text is persisted with explicit
`on_device_ocr` provenance. User confirmation of OCR data is provenance,
not admin verification.

## OCR and deterministic parsing

The runtime OCR is on-device ML Kit; the normal photo-first path never sends an
image to the text-normalization provider. `raw_ocr_text`, `source_segment`,
`source_language`, language confidence/method/version, OCR script,
`canonical_english`, candidates, nutrition observations, parser/prompt/model
provenance and review state are separate values. Translation never overwrites
the OCR source, and logs do not contain label text.

Known headings and labels are versioned data (`label_lexicon_v1`), not a closed
allowlist. Golden cases currently cover Italian, English, Finnish, Spanish,
French, German, Portuguese and Swedish. Other Latin-script languages can be
reported by ML Kit using a BCP-47-compatible code and continue through
structural parsing and the text fallback. No result is silently treated as
English: ambiguity is `und` (undetermined).

Without a known heading, the ingredient parser uses colons, comma/semicolon
lists, parentheses, percentages and document position. It stops before known
nutrition/storage/manufacturer noise and never uses a product title as an
ingredient list. Diacritics, allergen emphasis and percentages remain in source
evidence. Corrections such as `past4` → `pasta` are candidates with reason,
confidence and `needs_review`; they are never silent.

Nutrition is normalized to `energy_kj`, `energy_kcal`, `fat_g`,
`saturated_fat_g`, `carbohydrate_g`, `sugars_g`, `fibre_g`, `protein_g`,
`salt_g` and `sodium_mg`. Source label/value/unit, normalized value/unit, basis,
confidence and review state are retained. kJ/kcal and salt/sodium remain
distinct; comma/point decimals, split OCR rows, per-100 g, per-100 ml and serving
bases are supported. Ambiguous or implausible values stay empty or reviewable.

## Installed OCR scripts and MVP decision

The application explicitly constructs ML Kit with `TextRecognitionScript.latin`.
The Flutter plugin brings the Latin runtime as `implementation`; Chinese,
Devanagari, Japanese and Korean are only `compileOnly` in the plugin and are not
declared by the application, so they are **not installed capabilities**.

The final universal debug APK produced by `flutter build apk --debug` is
210,191,735 bytes. This debug/universal size is a test artifact, not a release
size or a measured per-module delta. Cached compressed AARs for the four optional recognizers total 8,577,872
bytes (Chinese 2,036,186; Devanagari 2,015,832; Japanese 2,626,220; Korean
1,899,634). Those AAR sizes are dependency-cost evidence, not a promised APK
delta; runtime-memory cost has not been measured. Given the observed low-memory
device failure, MVP installs Latin only. Other scripts are deferred. If detected
text uses an uninstalled script, the UI says `Sistema di scrittura non
supportato`, populates no fields and does not claim that language is supported.

## AI fallback status and cost control

The backend-only text fallback is wired through
`POST /mobile/dev/v1/capture/text-normalizations`. It is default-off through
`WYE_TEXT_NORMALIZATION_FALLBACK_ENABLED`; the local Phase 9 Compose stack turns
it on with the Fake provider. It accepts only source language, document type,
the necessary OCR segment, target `en`, schema and parser version. It accepts no
image, barcode, Product ID, mobile token, signed URL, personal data, log or full
product payload. No real OpenAI call is made by automated tests.

The cache fingerprint includes the segment SHA-256, source/document/target,
schema/parser/prompt versions and provider/model. Cache size and input length
are bounded; the mobile session permits at most two normalizations; provider
timeout is bounded and the OpenAI SDK is configured for at most one retry.
Complete deterministic results do not call the fallback. All fallback outputs
are forced to `needs_review=true`, even if a provider claims otherwise. Visual
AI fallback is deferred and is not part of ordinary Add Product.

## Unknown ingredients, science and scoring

Unknown ingredients are stored as non-authoritative product observations with a
pending mapping review. They do not create verified ingredients, substances,
ingredient-substance mappings, scientific evidence or hazard defaults. Existing
admin mapping-review APIs own candidate decision and alias approval.

EFSA/OpenFoodTox ingestion remains a separate, versioned administrative job.
There is no live scientific web lookup during scanning. Product runtime scoring
is not authorized by the current scientific contracts; missing evaluation is
shown as a canonical non-numeric unavailable/not-computable state. No legacy
`/analyze`, `/analyze-image`, placeholder score or new formula is used here.

## UX prototipo Phase 9.3A.3

La Home espone soltanto `Scansiona prodotto` e `Aggiungi prodotto`; lo storico
resta nella bottom navigation. `Aggiungi prodotto` apre `Analizza un'etichetta`,
disponibile anche al piano Base, e `Registra un nuovo prodotto`, che salva dati
da validare senza inventare score.

Le analisi AI esterne hanno quota giornaliera configurabile: Base 3, Premium
Light 50 e Premium Pro 100. OCR on-device, parser deterministico e cache hit non
consumano quota; una chiamata effettiva a un provider esterno billable consuma
una unità. Senza account reali il backend applica Base fail-closed.

La credenziale tecnica della facade non fa parte della UX. In dev/E2E Flutter
richiede automaticamente una capability breve, la conserva solo in memoria e la
rinnova quando serve. Non viene mostrata, copiata negli appunti, salvata nella
bozza o scritta nei log. L'autenticazione di produzione resta fuori scope.

Il feedback beta si invia dalle Impostazioni e viene persistito sanitizzato nel
database, senza immagini, barcode completo, OCR integrale, URL firmate o segreti.

## Known limits and manual gate

- Real packaging in every golden language still requires physical-device OCR
  testing; golden cases prove parser contracts, not universal language support.
- Draft fields, provenance and retained image paths are restored after restart;
  Android image-picker lost-data recovery also recovers a pending camera result.
- A verified-product conflict proposal payload/UI is still missing; overwrite is
  blocked instead.
- The local stack uses a conservative Fake text provider. Real-provider quality,
  cost and latency remain unverified and default-off outside explicit config.
- Recalculation after admin mapping approval remains a future slice.
- Features remain `IMPLEMENTED/AUTOMATED`, never `ACCEPTED`, until physical-device
  evidence passes.

## UX prototipo Phase 9.3A.4

- La navigazione è gerarchica: Home → Aggiungi prodotto → percorso scelto. Il
  tasto Android e la freccia AppBar hanno lo stesso comportamento; il wizard
  torna prima al passaggio precedente e salva automaticamente la bozza in uscita.
- Il ritaglio manuale è esclusivo della foto prodotto: crop libero, output JPEG
  massimo 2048×2048, qualità 88. Annullare non sostituisce la foto precedente.
- Ingredienti e tabella nutrizionale non vengono ritagliati: acquisizione fino a
  3072 px, qualità 94, controllo locale di risoluzione/luminosità/nitidezza e OCR
  ad alta leggibilità. Una foto sospetta viene richiesta di nuovo prima dell'AI.
- Le immagini non vengono inviate a OpenAI o a provider testuali. Solo testo
  sanitizzato può entrare nel fallback autorizzato e consumare quota.
- Ingredienti e nutrizione sono modificabili. Testo OCR originale, valori
  estratti e indicazione di correzione utente restano distinti nella bozza; ogni
  correzione resta `Da validare` e non crea mapping o score autorevoli.
- Energia kJ/kcal, sale/sodio, unità e base 100 g/100 ml/porzione sono distinti e
  validati con limiti fisicamente plausibili.
- Un emulatore Android con zero camera IDs non inizializza CameraX: mostra una
  guida recuperabile invece di terminare il processo Flutter.

## UX prototipo Phase 9.3A.4

- La navigazione è gerarchica: Home → Aggiungi prodotto → percorso scelto. Il
  tasto Android e la freccia AppBar hanno lo stesso comportamento; il wizard
  torna prima al passaggio precedente e salva automaticamente la bozza in uscita.
- Il ritaglio manuale è esclusivo della foto prodotto: crop libero, output JPEG
  massimo 2048×2048, qualità 88. Annullare non sostituisce la foto precedente.
- Ingredienti e tabella nutrizionale non vengono ritagliati: acquisizione fino a
  3072 px, qualità 94, controllo locale di risoluzione/luminosità/nitidezza e OCR
  ad alta leggibilità. Una foto sospetta viene richiesta di nuovo prima dell'AI.
- Le immagini non vengono inviate a OpenAI o a provider testuali. Solo testo
  sanitizzato può entrare nel fallback autorizzato e consumare quota.
- Ingredienti e nutrizione sono modificabili. Testo OCR originale, valori
  estratti e indicazione di correzione utente restano distinti nella bozza; ogni
  correzione resta `Da validare` e non crea mapping o score autorevoli.
- Energia kJ/kcal, sale/sodio, unità e base 100 g/100 ml/porzione sono distinti e
  validati con limiti fisicamente plausibili.
- Un emulatore Android con zero camera IDs non inizializza CameraX: mostra una
  guida recuperabile invece di terminare il processo Flutter.
