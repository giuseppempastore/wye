Certo. Ti preparo un **riassunto completo ma utilizzabile**, pensato proprio per essere incollato nella nuova chat del progetto WYE così da ripartire senza perdere contesto.

## Stato attuale del progetto WYE

WYE è un’app che deve permettere all’utente di **inquadrare un prodotto alimentare**, leggere barcode, ingredienti e valori nutrizionali, normalizzare gli ingredienti in un catalogo canonico e successivamente assegnare valutazioni scientifiche basate su fonti autorevoli, inizialmente soprattutto **EFSA/OpenFoodTox**.

L’obiettivo non è fare uno score “inventato dall’AI”, ma costruire un sistema **evidence-based, versionato, riproducibile e auditabile**.

### Obiettivo funzionale principale

Il flusso futuro desiderato è:

```text
foto prodotto
→ riconoscimento prodotto/barcode
→ foto ingredienti
→ foto tabella nutrizionale
→ OCR / modello multimodale
→ separazione corretta di:
   - ingredienti
   - valori nutrizionali
   - allergeni
   - quantità/unità
→ normalizzazione multilingua
→ mapping su ingredienti canonici Wye
→ eventuale mapping su sostanze scientifiche/regolatorie
→ assessment scientifico EFSA
→ scoring Wye deterministico e versionato
```

Il backend deve essere in grado di gestire etichette in più lingue. L’interfaccia dell’app può inizialmente supportare poche lingue, ad esempio italiano e inglese, ma il parser/AI dovrebbe essere linguisticamente agnostico.

---

# Principi architetturali già decisi

## 1. L’AI non è la source of truth scientifica

L’AI può:

* leggere immagini
* estrarre ingredienti
* distinguere ingredienti/nutrizione/allergeni
* tradurre semanticamente
* proporre mapping
* proporre candidati

L’AI **non deve**:

* inventare nuovi ingredienti canonici senza governance
* creare automaticamente equivalenze dubbie
* decidere autonomamente lo score scientifico
* considerare assenza di evidenza = rischio
* diventare la fonte scientifica primaria

---

## 2. Normalizzazione ingredienti

Il database Wye deve avere ingredienti canonici in inglese.

Esempi:

```text
cacao in polvere
Kakaopulver
poudre de cacao
cocoa powder
powdered cocoa
```

devono poter convergere tutti verso:

```text
cocoa powder
```

mentre:

```text
cocoa butter
```

deve restare un ingrediente diverso.

La pipeline desiderata è:

```text
raw ingredient
→ lookup deterministico su alias già conosciuti
→ se trovato: mapping diretto
→ se non trovato: AI propone candidati
→ se ambiguo: needs_review
→ se validato: mapping canonico
```

Gli alias approvati devono essere riutilizzati in futuro senza richiamare l’AI.

L’AI non deve creare automaticamente nuovi record in `ingredients`.

---

# Integrità dei dati prodotto

È stato deciso che l’utente **non deve avere ampio margine per modificare direttamente i dati del prodotto**, perché potrebbe involontariamente o volontariamente alterare ingredienti o valori nutrizionali e falsare lo score.

Per questo le immagini originali sono considerate evidenza primaria.

Devono essere acquisite e conservate separatamente:

* foto principale/frontale del prodotto
* foto lista ingredienti
* foto tabella nutrizionale

Il barcode invece:

* viene letto
* salvato come valore testuale
* usato per ricerca/precompilazione
* **non viene salvato come immagine**

La foto principale serve anche a mostrare il prodotto nello storico e quando viene trovato via barcode, per aiutare l’utente a capire se è il prodotto corretto.

---

# Strategia immagini

È stato deciso:

```text
Object Storage
→ immagini vere

PostgreSQL
→ metadata, checksum, provenance, storage reference
```

Quindi niente `BYTEA` per le immagini principali.

Motivazioni:

* DB più leggero
* backup più semplici
* migliore scalabilità
* possibilità futura di CDN
* riesecuzione OCR/AI
* audit e provenance

Possibili storage futuri:

* S3
* Cloudflare R2
* Supabase Storage
* MinIO
* equivalente

---

# Modello dati immagini proposto

Nuova tabella:

```text
product_images
```

Campi concettuali:

```text
id
product_id
image_type
storage_reference
mime_type
byte_size
checksum
source
status
is_current
captured_at
created_at
superseded_at
superseded_by_image_id
provenance
```

Tipi immagini:

```text
product_front
ingredients
nutrition
other
```

Le immagini sono append-only/versionabili.

Non devono essere sovrascritte in modo distruttivo.

---

# OCR / extraction provenance

È stato deciso di introdurre un livello tra immagine e dati normalizzati.

## `product_label_documents`

Conserva il testo OCR/raw derivato da una specifica immagine.

Campi concettuali:

```text
id
product_id
product_image_id
raw_text
detected_language
source_type
source_checksum
created_at
```

Il `raw_text` non deve essere sovrascritto.

---

## `label_extraction_runs`

Registra una specifica elaborazione OCR/AI.

Campi:

```text
id
label_document_id
extraction_method
provider
model_name
model_version
prompt_version
raw_response
run_status
created_at
```

Serve a sapere:

* quale AI è stata usata
* quale versione
* quale prompt
* quale risposta grezza
* quando

Così in futuro la stessa immagine può essere rielaborata da un modello migliore.

---

## `label_extraction_items`

Serve a separare correttamente i dati estratti.

Tipi:

```text
ingredient
ingredient_list
nutrition
allergen
quantity
unit
other
```

Campi concettuali:

```text
raw_text
normalized_text
detected_language
structured_value
unit
position_in_document
extraction_confidence
extraction_status
```

Questo serve precisamente a evitare i “mischioni” tra ingredienti e tabella nutrizionale.

---

# Ingredienti canonici e alias

Si riutilizza:

```text
ingredients
ingredient_aliases
```

`ingredients` resta il catalogo canonico Wye.

`ingredient_aliases` deve diventare la tabella degli alias multilingua già validati.

Esempio:

```text
cacao in polvere | it → cocoa powder
Kakaopulver      | de → cocoa powder
poudre de cacao  | fr → cocoa powder
powdered cocoa   | en → cocoa powder
```

Alias ambigui/non verificati non devono diventare automaticamente alias accettati.

---

# Occorrenza ingredienti nei prodotti

La tabella esistente:

```text
product_ingredients
```

deve essere evoluta per conservare il mapping.

Campi/concetti previsti:

```text
ingredient_id nullable
label_extraction_item_id
normalized_text
detected_language
mapping_method
mapping_confidence
mapping_status
mapping_review_id
mapping_provenance
```

Stati possibili:

```text
accepted
needs_review
ambiguous
unmapped
rejected
```

Se il mapping non è certo:

```text
ingredient_id = NULL
```

e non viene assegnato nessun rischio arbitrario.

---

# Review dei mapping

Sono state proposte:

```text
ingredient_mapping_reviews
ingredient_mapping_review_candidates
```

Servono quando l’AI non riesce a determinare con certezza l’ingrediente canonico.

Il sistema deve conservare:

* testo originale
* lingua
* candidati
* confidence
* metodo
* motivazione
* stato review
* eventuale candidato selezionato

Una review ambigua non può creare automaticamente un alias.

---

# Ingredienti Wye e sostanze scientifiche/regolatorie

È stata presa una decisione importante:

```text
ingrediente Wye != necessariamente sostanza regolatoria
```

Per questo sono previste:

```text
substances
substance_identifiers
ingredient_substances
```

`substances` rappresenta l’entità scientifica/regolatoria.

`substance_identifiers` contiene:

* E-number
* CAS
* EC
* FL number
* altri identificatori ufficiali

`ingredient_substances` gestisce la relazione N:M tra ingrediente Wye e sostanza regolatoria.

Questo è necessario per EFSA/OpenFoodTox.

---

# Fonti e dataset scientifici

Si mantiene:

```text
sources
```

e si aggiungono:

```text
source_datasets
source_dataset_releases
```

Motivo:

```text
EFSA
```

non è la stessa cosa di:

```text
OpenFoodTox release X
```

Ogni release deve poter avere:

* versione
* data pubblicazione
* data acquisizione
* URL
* checksum
* formato
* licenza
* stato importazione

---

# Assessment scientifici

Sono state proposte:

```text
scientific_assessments
scientific_assessment_findings
```

Un assessment:

```text
substance
→ dataset release
→ assessment
→ findings
```

Può conservare:

* assessment type
* assessment version
* published_at
* valid_from
* valid_to
* external document reference
* conclusion
* payload strutturato
* checksum/external ID

I findings possono contenere:

* endpoint
* valore
* unità
* popolazione/contesto
* tipo evidenza
* conclusione

Ma **nessun assessment produce automaticamente uno score Wye**.

---

# Strategia scientifica

Per la V1 è stato deciso di **non partire da PubMed come fonte primaria**.

Approccio preferito:

```text
EFSA / OpenFoodTox
→ fonte scientifica primaria

Commissione Europea
→ stato regolatorio/autorizzativo

PubMed / Europe PMC
→ eventualmente fase futura / early warning
```

Motivo:

i singoli paper possono essere contraddittori, revisionati, deboli o non rappresentativi.

EFSA ha già un processo di risk assessment e sintesi delle evidenze.

---

# Scoring

Lo score NON è ancora stato definito.

È stato deciso che dovrà essere:

* deterministico
* riproducibile
* versionato
* spiegabile
* basato su dati strutturati

E deve separare almeno:

```text
Safety Score
Evidence Confidence
```

Caso senza evidenza sufficiente:

```text
score = null
assessment_status = insufficient_evidence
```

Non:

```text
score basso
```

L’assenza di evidenza non è evidenza di rischio.

---

# Storia/versionamento score

In futuro bisognerà avere uno storico.

Concetto:

```text
ingredient_score_history
```

Ogni score dovrà essere riconducibile a:

```text
ingredient
→ assessment
→ dataset/versione
→ scoring model version
→ input
→ risultato
→ timestamp
```

---

# Batch periodico futuro

È previsto un job tipo:

```text
fetch latest EFSA/OpenFoodTox
→ compare hash/version
→ detect changes
→ identify affected substances
→ affected ingredients
→ recompute only affected scores
→ save history
→ changelog
```

Non bisogna ricalcolare tutto il catalogo se la fonte non è cambiata.

---

# Stato migration DB

La Fase 1 è già stata completata con successo da Codex.

È stato introdotto Alembic.

File creati/modificati:

```text
backend/requirements.txt
backend/alembic.ini
backend/migrations/env.py
backend/migrations/script.py.mako
backend/migrations/versions/0001_initial_schema.py
backend/scripts/baseline_existing_db.py
postgres/MIGRATIONS.md
```

Alembic è stato scelto senza convertire l’app a SQLAlchemy ORM.

Lo stack backend resta:

```text
FastAPI
psycopg2
PostgreSQL
```

---

# Verifiche Fase 1 completate

Codex ha verificato:

```text
alembic upgrade head
```

su PostgreSQL vuoto.

Schema risultante verificato contro il legacy:

```text
187 colonne
30 indici
185 vincoli
schema_match = ok
```

È stata verificata anche l’adozione di un DB esistente tramite `alembic stamp`.

Dati preesistenti preservati.

Test:

```text
12/12 OK
```

Import backend:

```text
app_import = ok
```

I DB temporanei usati per test sono stati rimossi.

---

# Problema architetturale già rilevato

Attualmente WYE ha due fonti concorrenti di verità:

```text
catalogo Python statico
+
PostgreSQL
```

In futuro bisognerà eliminare gradualmente questa duplicazione.

Il catalogo scientifico/rischio non deve restare hard-coded in Python.

La source of truth futura deve essere PostgreSQL.

---

# Migration successiva

La prossima migration sarà:

```text
0002_scientific_data_model
```

Il piano corrente è di includere:

```text
product_images
product_label_documents
label_extraction_runs
label_extraction_items

substances
substance_identifiers
ingredient_substances

source_datasets
source_dataset_releases

scientific_assessments
scientific_assessment_findings

ingredient_mapping_reviews
ingredient_mapping_review_candidates

estensione ingredient_aliases
estensione product_ingredients
```

È stato deciso invece di **NON implementare ancora**:

```text
product_data_overrides
```

La gestione delle correzioni manuali utente verrà affrontata più avanti.

---

# Cosa NON deve fare ancora la migration 0002

Niente:

* OCR
* Vision
* AI
* upload immagini
* object storage reale
* frontend
* EFSA ingestion
* scoring
* refactoring non necessario
* modifiche distruttive

Deve essere solo un’evoluzione additiva del modello dati.

---

# Prompt già deciso per Codex

Il prossimo task operativo è:

```text
Approvo il modello aggiornato.

Procedi con l'implementazione della migration `0002_scientific_data_model`, con una sola modifica:

NON implementare ancora `product_data_overrides`.
La gestione delle correzioni manuali verrà affrontata in una fase successiva.

Implementa invece:

- product_images
- product_label_documents
- label_extraction_runs
- label_extraction_items
- substances
- substance_identifiers
- ingredient_substances
- source_datasets
- source_dataset_releases
- scientific_assessments
- scientific_assessment_findings
- ingredient_mapping_reviews
- ingredient_mapping_review_candidates
- estensioni additive a ingredient_aliases
- estensioni additive a product_ingredients

Vincoli:
- migration additive;
- nessuna perdita dati;
- nessun OCR;
- nessuna AI;
- nessun upload;
- nessuna UI;
- nessuna EFSA ingestion;
- nessuno scoring;
- nessun refactoring non necessario.

Le immagini devono essere referenziate tramite object storage, non salvate come BYTEA.

Al termine:
1. esegui migration su database vuoto;
2. esegui migration su database baseline esistente;
3. verifica rollback/downgrade dove possibile;
4. esegui i test esistenti;
5. aggiungi test per i nuovi vincoli critici;
6. mostra file modificati, comandi eseguiti e risultati.

Non modificare README.md o il frontend in questa fase.
```

---

# Modello AI consigliato per Codex

Per il lavoro quotidiano:

```text
Terra Medium
```

È il default consigliato.

Per:

* migration
* backend
* test
* API
* refactoring normale

→ Terra Medium.

Per decisioni architetturali molto complesse:

```text
Sol
```

Per piccoli task meccanici:

```text
Luna
```

Per la migration `0002` è sufficiente **Terra Medium**.

---

## Next step esatto nella nuova chat

Riparti dicendo:

> “Questo è il contesto completo del progetto WYE. La Fase 1 Alembic è conclusa. Il prossimo step è implementare e revisionare la migration `0002_scientific_data_model`. Voglio continuare da qui senza cambiare l’architettura già decisa.”

E poi incolla questo riassunto.

Da lì il passo successivo sarà **far implementare a Codex la `0002`, analizzare insieme il risultato, e solo dopo iniziare la vera pipeline di acquisizione immagini/OCR/AI.**
