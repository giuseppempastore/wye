# WYE — Validazione End-to-End della Fase 4

## Stato finale

**FASE 4 VALIDATA END-TO-END CON PROVIDER OPENAI REALE**

Data test:

```text
28 agosto 2026
```

Branch:

```text
ingredients_score
```

Commit Fase 4:

```text
beac55c76f506ec1d480104e9388466474c55af7
Fase 4 - Add label extraction pipeline
```

La validazione ha verificato realmente entrambi i rami principali della Fase 4:

```text
ingredients ✅
nutrition   ✅
```

Il test non ha utilizzato solamente mock o fake provider: sono state eseguite chiamate reali alla OpenAI Responses API su immagini reali caricate nello storage locale MinIO.

---

# 1. Obiettivo della validazione

Verificare realmente il percorso:

```text
immagine reale
→ upload API WYE
→ MinIO
→ finalize
→ storage_objects
→ product_images
→ download privato backend
→ OpenAI Responses API
→ Structured Outputs
→ validazione Pydantic
→ label_extraction_runs
→ label_extraction_items
→ risposta API
```

L'obiettivo era confermare che la Fase 4 funzionasse non soltanto nei test automatici ma anche in una esecuzione locale reale.

---

# 2. Ambiente Python

Il primo virtual environment provato era:

```text
C:\Projects\wye\.venv
```

Questo ambiente utilizzava Python 3.12 e non conteneva inizialmente OpenAI.

Tentando l'installazione dei requirements, l'installazione si è bloccata su:

```text
psycopg2-binary==2.9.7
```

con errore:

```text
Microsoft Visual C++ 14.0 or greater is required
```

Non sono stati installati Build Tools e non sono state modificate le dipendenze.

È stato invece utilizzato il virtual environment backend già coerente con il progetto:

```text
C:\Projects\wye\backend\venv
```

Verifiche:

```text
OpenAI: 1.109.1
HTTPX: 0.28.1
Responses API: True
```

Quindi:

```text
openai==1.109.1 ✅
httpx==0.28.1   ✅
client.responses ✅
```

---

# 3. Configurazione OpenAI

La chiave API già esistente sul sistema era:

```text
WYE_OPENAI_KEY
```

La nuova pipeline Fase 4 utilizza:

```text
WYE_OPENAI_API_KEY
```

Per il test è stato quindi creato un alias soltanto nella sessione PowerShell:

```powershell
$env:WYE_OPENAI_API_KEY = $env:WYE_OPENAI_KEY
```

Configurazione extraction:

```text
WYE_EXTRACTION_PROVIDER=openai
WYE_OPENAI_EXTRACTION_MODEL=gpt-4o-mini
WYE_EXTRACTION_TIMEOUT_SECONDS=90
```

Nessuna chiave API è stata inserita nel repository.

---

# 4. Database isolato

Per evitare qualunque modifica al database storico `wye` è stato utilizzato:

```text
wye_e2e
```

Variabili principali:

```text
PGHOST=localhost
PGPORT=5432
PGUSER=postgres
PGDATABASE=wye_e2e
```

Alembic:

```text
0005_label_extraction_pipeline (head)
```

Verifica PostgreSQL diretta:

```sql
SELECT version_num FROM alembic_version;
```

Risultato:

```text
0005_label_extraction_pipeline
```

Il database storico non è stato utilizzato.

---

# 5. Object storage locale

Docker non era disponibile sul computer.

È stato quindi utilizzato MinIO nativo per Windows.

Endpoint:

```text
http://localhost:9000
```

Console:

```text
http://localhost:9001
```

Bucket:

```text
wye-private
```

Verifica TCP:

```text
TcpTestSucceeded : True
```

Configurazione WYE:

```text
WYE_STORAGE_PROVIDER=minio
WYE_STORAGE_ENDPOINT=http://localhost:9000
WYE_STORAGE_BUCKET=wye-private
WYE_STORAGE_REGION=us-east-1
WYE_STORAGE_FORCE_PATH_STYLE=true
```

---

# 6. Backend FastAPI

Il backend è stato avviato tramite Uvicorn su:

```text
http://127.0.0.1:8000
```

Health check:

```text
status = ok
```

---

# 7. Test reale — Ingredients

È stata utilizzata una vera immagine JPEG contenente una lista ingredienti.

Prima dell'upload sono stati calcolati:

```text
byte size
SHA-256
```

L'upload è stato inizializzato tramite:

```text
POST /products/{product_id}/images/uploads
```

con:

```text
image_type = ingredients
mime_type  = image/jpeg
byte_size
sha256
```

Il backend ha restituito un signed PUT URL e l'immagine è stata caricata realmente su MinIO.

Finalize:

```text
status = finalized
storage_object_id = 1
product_image_id = 1
```

---

# 8. Primo tentativo OpenAI — errore quota

La prima extraction reale ha prodotto:

```text
run_status = failed
error_code = provider_error
items = []
```

Un test diretto della Responses API ha restituito:

```text
HTTP 429
insufficient_quota
```

Questo ha dimostrato che:

```text
pipeline WYE        ✅
gestione errori     ✅
zero item parziali  ✅
OpenAI billing      ❌ credito non disponibile
```

Non è stata modificata la pipeline per questo errore.

---

# 9. Attivazione credito API

La pagina Billing mostrava inizialmente:

```text
Credit remaining: $0.00
```

È stato successivamente aggiunto credito API:

```text
API credit balance: $5.00
Pay as you go
```

Dopo l'attivazione del credito è stato ripetuto il test reale.

---

# 10. Extraction reale — Ingredients

È stata utilizzata una nuova `Idempotency-Key`.

Risultato:

```text
run_status = succeeded
provider = openai
model_name = gpt-4o-mini-2024-07-18
error_code = null
error_detail = null
provider_request_id = presente
```

Sono stati persistiti:

```text
1 ingredient_list
15 ingredient
5 allergen
```

Totale:

```text
21 label_extraction_items
```

Allergeni estratti:

```text
latte
uova
nocciole
frutta a guscio
soia
```

Consumo:

```text
input_tokens  = 26.080
output_tokens = 644
total_tokens  = 26.724
```

---

# 11. Osservazioni dal test ingredients

Sono emersi alcuni miglioramenti non bloccanti:

```text
PuÃ² contenere
```

al posto di:

```text
Può contenere
```

Possibile problema di encoding/mojibake.

Inoltre percentuali visibili come:

```text
cacao in polvere 9%
cioccolato fondente nella crema 2.5%
```

sono rimaste nel `raw_text`, ma il campo strutturato `quantity` è rimasto `null`.

È inoltre emersa una segmentazione da verificare:

```text
farina di riso: amido di mais
```

---

# 12. Test reale — Nutrition

È stata caricata una seconda vera immagine JPEG con:

```text
image_type = nutrition
```

Il flusso ha ripetuto:

```text
initialize
→ signed PUT
→ MinIO
→ finalize
→ product_image
→ extraction OpenAI
```

È stata usata una nuova `Idempotency-Key`.

Risultato:

```text
run_status = succeeded
provider = openai
model_name = gpt-4o-mini-2024-07-18
error_code = null
error_detail = null
provider_request_id = presente
```

Sono stati creati:

```text
16 label_extraction_items
```

tutti di tipo:

```text
nutrition
```

---

# 13. Dati nutrizionali estratti

## Per 100 g

```text
energy          2056 kJ
fat             23.5 g
saturated_fat   10.5 g
carbohydrate    60.9 g
sugars          24 g
fiber            4.0 g
protein          7.0 g
salt             0.625 g
```

## Per biscotto

```text
energy           226 kJ
fat               2.6 g
saturated_fat     1.2 g
carbohydrate      6.7 g
sugars             2.6 g
fiber              0.4 g
protein            0.7 g
salt               0.069 g
```

La pipeline ha quindi distinto correttamente:

```text
per_100_g
per_serving
```

---

# 14. Informazioni lette ma non completamente strutturate

Il `raw_text` conteneva anche:

```text
2056 kJ
491 kcal
226 kJ
54 kcal
%AR
per 100g
per biscotto (11g)
```

ma lo structured output ha salvato soltanto i valori energetici in kJ.

Quindi:

```text
491 kcal → letto nel raw_text, non strutturato
54 kcal  → letto nel raw_text, non strutturato
```

La basis è stata classificata correttamente, ma:

```text
per_100_g:
quantity = null
unit = null
```

e:

```text
per_serving:
raw_text = "per biscotto (11g)"
quantity = null
unit = null
```

anche se `100 g` e `11 g` erano visibili.

La colonna `%AR` è stata trascritta nel raw text, ma non fa parte dello schema nutrition corrente.

Consumo:

```text
input_tokens  = 14.747
output_tokens = 1.034
total_tokens  = 15.781
```

---

# 15. Risultato complessivo E2E

## Infrastructure

```text
Python environment              ✅
OpenAI SDK                      ✅
HTTPX                           ✅
PostgreSQL                      ✅
Alembic 0005                    ✅
Database isolato                ✅
MinIO Windows                   ✅
Bucket privato                  ✅
FastAPI                         ✅
Health check                    ✅
```

## Fase 3 integration

```text
signed PUT                      ✅
staging                         ✅
SHA-256                         ✅
finalize                        ✅
storage_objects                 ✅
product_images                  ✅
```

## Fase 4

```text
private image download          ✅
OpenAI Responses API            ✅
Structured Outputs              ✅
Pydantic validation             ✅
label documents                 ✅
extraction runs                 ✅
atomic item persistence         ✅
idempotency                     ✅
provider provenance             ✅
error handling                  ✅
```

## Functional branches

```text
ingredients extraction          ✅
allergen extraction             ✅
nutrition extraction            ✅
per-100-g basis                 ✅
per-serving basis               ✅
```

---

# 16. Error handling verificato realmente

Il primo errore OpenAI ha dimostrato:

```text
provider failure
→ run failed
→ error_code
→ error_detail sanitizzato
→ zero item parziali
```

Il successivo run, con nuova Idempotency-Key, ha avuto successo.

---

# 17. Limiti emersi

Non bloccanti per la conclusione della Fase 4:

```text
encoding "PuÃ²"                         ⚠️
ingredient percentages → quantity null ⚠️
energy kcal non strutturate            ⚠️
basis quantity/unit non compilate      ⚠️
%AR non strutturata                    ⚠️
segmentazione ingredienti da benchmark ⚠️
```

Questi aspetti riguardano qualità dello schema/prompt e benchmarking, non il funzionamento della pipeline.

Possono essere affrontati in una Fase 4.1 oppure quando il dominio successivo richiederà esplicitamente questi dati.

---

# 18. Cosa NON è stato fatto

La validazione non ha introdotto:

```text
normalizzazione ingredienti
ingredient aliases
product ingredients
mapping scientifico
EFSA
OpenFoodTox
scoring
```

La separazione prevista resta:

```text
Fase 4 = estrazione
Fase 5 = normalizzazione/mapping
```

---

# 19. Conclusione

Entrambi i percorsi principali sono stati eseguiti con successo su immagini reali e provider OpenAI reale:

```text
INGREDIENTS
immagine reale
→ OpenAI
→ ingredient list
→ ingredient items
→ allergen items
→ PostgreSQL
✅

NUTRITION
immagine reale
→ OpenAI
→ nutrition rows
→ per-100-g / per-serving
→ PostgreSQL
✅
```

Pertanto:

# ✅ FASE 4 CONCLUSA E VALIDATA END-TO-END

La fase successiva può concentrarsi sulla trasformazione del testo estratto in entità canoniche WYE:

```text
Fase 5 — Normalizzazione e Review Mapping
```
