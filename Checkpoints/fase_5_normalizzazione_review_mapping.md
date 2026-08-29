# WYE — Fase 5: Normalizzazione e Review Mapping

## Stato

**FASE 5 COMPLETATA + E2E**

Branch:

```text
ingredients_score
```

Commit Fase 4 di riferimento:

```text
beac55c76f506ec1d480104e9388466474c55af7
Fase 4 - Add label extraction pipeline
```

Alembic head al termine della Fase 4:

```text
0005_label_extraction_pipeline
```

La Fase 4 è conclusa e validata end-to-end con immagini reali, MinIO locale, PostgreSQL e OpenAI reale.

La Fase 5 parte dai risultati strutturati prodotti dalla Fase 4 e introduce la trasformazione:

```text
label_extraction_item
        ↓
testo ingrediente normalizzato
        ↓
candidate mapping
        ↓
review
        ↓
canonical WYE ingredient
```

La Fase 5 NON introduce ancora fonti scientifiche, EFSA/OpenFoodTox o scoring.

---

# 1. Obiettivo della Fase 5

La Fase 5 deve rispondere alla domanda:

```text
"Quale ingrediente canonico WYE rappresenta
questo ingrediente letto dall'etichetta?"
```

La Fase 4 risponde invece a:

```text
"Cosa c'è scritto sull'etichetta?"
```

Le fasi successive risponderanno a:

```text
"Quali evidenze scientifiche esistono per questo ingrediente?"
```

e successivamente:

```text
"Come contribuisce questo ingrediente allo score del prodotto?"
```

La separazione concettuale deve quindi essere:

```text
FASE 4
immagine
→ testo estratto

FASE 5
testo estratto
→ ingrediente canonico

FASE 6
ingrediente / sostanza
→ evidenze scientifiche

FASE 7
evidenze scientifiche
→ scoring
```

---

# 2. Punto di partenza

La Fase 4 produce record:

```text
label_extraction_items
```

Tra questi sono presenti item con:

```text
item_type = ingredient
```

Ogni item conserva il testo estratto dall'etichetta e la provenance dell'estrazione.

La Fase 5 deve partire esclusivamente da questi dati senza modificare retroattivamente il risultato della Fase 4.

Il principio è:

```text
raw extraction
≠
normalizzazione
≠
mapping canonico
```

Questi tre livelli devono rimanere distinguibili e auditabili.

---

# 3. Modello dati già disponibile

Le Fasi 2 e 2.1 hanno già predisposto gran parte dello schema necessario.

Tabelle principali:

```text
ingredients
ingredient_aliases
product_ingredients
ingredient_mapping_reviews
ingredient_mapping_review_candidates
```

`ingredients` rappresenta il catalogo canonico WYE.

`ingredient_aliases` rappresenta forme alternative conosciute di un ingrediente.

`product_ingredients` rappresenta gli ingredienti effettivamente osservati su uno specifico prodotto.

`ingredient_mapping_reviews` rappresenta il processo di review di un mapping.

`ingredient_mapping_review_candidates` contiene i possibili ingredienti canonici candidati.

La Fase 5 deve riutilizzare questo modello senza creare un sistema parallelo.

---

# 4. Flusso generale previsto

```text
label_extraction_items
item_type = ingredient
        │
        ▼
IngredientNormalizer
        │
        ▼
normalized_text
        │
        ▼
CandidateGenerator
        │
        ├── ingredients
        │
        └── ingredient_aliases
        │
        ▼
product_ingredients
        │
        ▼
ingredient_mapping_reviews
        │
        ▼
ingredient_mapping_review_candidates
        │
        ▼
Review / deterministic resolution
        │
 ┌──────┼──────────┐
 ▼      ▼          ▼
accepted ambiguous rejected
 │
 ▼
ingredient_id
 │
 ▼
canonical WYE ingredient
```

---

# 5. Principio fondamentale: non perdere il dato originale

La pipeline deve mantenere distinti almeno:

```text
raw_text
normalized_text
canonical ingredient
```

Esempio:

```text
raw_text:
"  ACIDO   CITRICO "

normalized_text:
"acido citrico"

canonical ingredient:
Acido citrico
```

Altro esempio:

```text
raw_text:
"E 330"

normalized_text:
"e330"

canonical ingredient:
Acido citrico
```

La trasformazione:

```text
"E 330"
→
"e330"
```

è normalizzazione deterministica.

La trasformazione:

```text
"e330"
→
"Acido citrico"
```

è mapping canonico.

Le due operazioni devono rimanere separate.

---

# 6. Normalizzazione

La normalizzazione deve essere:

- deterministica;
- versionata;
- idempotente;
- indipendente da OpenAI;
- indipendente dal database;
- priva di interpretazioni semantiche.

Versione iniziale prevista:

```text
ingredient_normalization_v1
```

Regole iniziali previste:

```text
Unicode normalization
case folding
trim
whitespace normalization
apostrofi tipografici equivalenti
trattini tipografici equivalenti
normalizzazione grafica E-number
```

Esempi:

```text
"  ACIDO   CITRICO "
→ "acido citrico"

"E 330"
→ "e330"

"E-330"
→ "e330"

"LECITINA DI SOIA"
→ "lecitina di soia"
```

Non devono essere effettuate trasformazioni semantiche.

Esempio vietato:

```text
"olio vegetale"
→
"olio di palma"
```

---

# 7. Candidate generation

Dopo la normalizzazione vengono cercati possibili ingredienti canonici.

Le candidate source iniziali devono essere:

```text
ingredients
```

e:

```text
ingredient_aliases
```

limitatamente agli alias validi/accettati secondo lo schema.

Strategia iniziale prevista:

```text
1. exact accepted alias match
2. exact canonical name match
3. deterministic variants
4. conservative fuzzy matching
```

Il fuzzy matching deve servire inizialmente soltanto a proporre candidati.

Non deve automaticamente stabilire la verità canonica.

---

# 8. Candidate confidence

La confidence del mapping è distinta dalla confidence dell'estrazione.

Esempio:

```text
extraction confidence = 0.99
mapping confidence    = 0.52
```

Questo significa:

```text
il testo è stato letto correttamente
ma il significato canonico rimane ambiguo
```

Non combinare automaticamente i due valori.

---

# 9. Product ingredient

Per ogni `label_extraction_item` di tipo `ingredient` deve poter essere materializzato un:

```text
product_ingredient
```

contenente almeno concettualmente:

```text
product_id
label_extraction_item_id
raw_name
normalized_text
detected_language
position_in_list
ingredient_id
mapping_method
mapping_status
mapping_provenance
```

Prima della risoluzione canonica:

```text
ingredient_id = NULL
```

deve essere un caso valido.

Questo significa:

```text
"WYE sa che l'ingrediente è presente,
ma non ha ancora stabilito quale ingrediente canonico rappresenti."
```

---

# 10. Mapping status

La pipeline deve poter rappresentare esplicitamente almeno casi equivalenti a:

```text
unmapped
pending / needs_review
accepted
ambiguous
rejected
```

La terminologia definitiva deve rispettare i valori già definiti nello schema corrente.

Non tutti gli ingredienti devono necessariamente essere risolti.

La possibilità di rappresentare:

```text
"non lo sappiamo"
```

è un requisito di progetto.

---

# 11. Review mapping

Quando un mapping non può essere risolto deterministicamente con sufficiente sicurezza viene creata una review.

Schema già disponibile:

```text
ingredient_mapping_reviews
ingredient_mapping_review_candidates
```

Gli stati review già previsti includono:

```text
pending
accepted
ambiguous
rejected
```

I candidate devono puntare esclusivamente a:

```text
ingredients
```

e NON direttamente a:

```text
substances
```

Il mapping della Fase 5 è quindi:

```text
label ingredient
→
canonical WYE ingredient
```

Non:

```text
label ingredient
→
substance
```

---

# 12. Review accepted

Una review `accepted` deve identificare esattamente un ingrediente canonico.

L'invariante DB già introdotta nella Fase 2.1 stabilisce che una review accepted debba avere esattamente un candidate selezionato.

La decisione deve aggiornare coerentemente:

```text
ingredient_mapping_review_candidates.is_selected
ingredient_mapping_reviews.review_status
ingredient_mapping_reviews.reviewed_by
ingredient_mapping_reviews.reviewed_at
product_ingredients.ingredient_id
product_ingredients.mapping_method
product_ingredients.mapping_status
product_ingredients.mapping_provenance
```

L'operazione dovrà essere atomica.

---

# 13. Mapping ambiguo

Esempio:

```text
"olio vegetale"
```

potrebbe avere candidate:

```text
olio di palma
olio di girasole
olio di colza
```

Se l'etichetta non permette di scegliere correttamente:

```text
mapping_status = ambiguous
ingredient_id = NULL
```

Il sistema non deve inventare un mapping.

---

# 14. Mapping rejected / unmapped

Se nessun ingrediente canonico disponibile rappresenta correttamente il testo:

```text
ingredient_id = NULL
```

deve rimanere possibile.

La pipeline non deve creare automaticamente nuovi canonical ingredients soltanto per poter completare il mapping.

---

# 15. Auto-accept

La prima versione deve essere molto conservativa.

È accettabile automatizzare soltanto mapping deterministicamente univoci, ad esempio:

```text
accepted exact alias
+
un solo canonical ingredient possibile
```

Non usare inizialmente una semplice soglia generica del tipo:

```text
confidence > X
→ auto-accept
```

per fuzzy matching o AI.

Fuzzy e sistemi probabilistici devono inizialmente produrre candidate da sottoporre a review.

---

# 16. AI nella Fase 5

OpenAI NON è necessario come primo motore di normalizzazione o mapping.

La strategia iniziale è:

```text
deterministic normalization
+
exact matching
+
alias lookup
+
conservative fuzzy candidate generation
```

Un futuro provider AI potrà eventualmente essere introdotto dietro un'interfaccia sostituibile se benchmark reali dimostreranno che aggiunge valore.

L'AI potrà proporre candidati.

Non dovrà diventare automaticamente l'autorità canonica.

---

# 17. Alias learning

Una review umana accepted potrà eventualmente produrre un nuovo:

```text
ingredient_alias
```

Esempio:

```text
"acido citrico (E330)"
→
Acido citrico
```

Ma l'alias learning NON deve essere automatico per ogni accepted mapping.

L'approvazione di un alias deve essere esplicita e mantenere provenance.

Possibile comportamento futuro:

```text
approve_as_alias = true
```

o endpoint equivalente.

---

# 18. Provenance

Ogni mapping deve essere ricostruibile.

Catena prevista:

```text
product_ingredient
        ↓
label_extraction_item
        ↓
label_extraction_run
        ↓
product_label_document
        ↓
product_image
        ↓
storage_object
```

La Fase 4 conserva già:

```text
provider
model
prompt
schema version
prompt hash
request provenance
```

La Fase 5 deve aggiungere informazioni equivalenti per il mapping, ad esempio:

```text
normalization_version
candidate_generation_version
mapping_method
candidate_confidence
review_status
reviewer
review_timestamp
selected_candidate
```

L'obiettivo è poter spiegare in futuro:

```text
"Perché WYE considera questo testo
come questo specifico ingrediente?"
```

---

# 19. Idempotenza

Un determinato:

```text
label_extraction_item
```

deve materializzarsi al massimo una volta come:

```text
product_ingredient
```

Quindi:

```text
same extraction item
→
same product ingredient
```

Una nuova extraction run produce invece nuovi extraction item e può quindi generare un nuovo mapping indipendente.

---

# 20. Fase 5.1 — Mapping Integrity & Schema Hardening

## Stato

**COMPLETATA**

Obiettivo:

blindare le invarianti DB necessarie prima di costruire la pipeline applicativa.

Migration:

```text
0006_mapping_integrity_hardening
```

Sono state introdotte:

```text
uq_product_ingredients_label_extraction_item
```

che garantisce unicità di:

```text
label_extraction_item_id
```

quando non NULL.

E:

```text
uq_mapping_reviews_pending_product_ingredient
```

che garantisce al massimo una review pending per ogni product ingredient.

Sono state preservate le invarianti della Fase 2.1 relative alle review accepted.

Test specifici dichiarati:

```text
9 / 9 passed
```

Migration lifecycle verificato:

```text
0005 → 0006 ✅
0006 → 0005 ✅
0005 → 0006 ✅
```

---

# 21. Fase 5.2 — Deterministic Ingredient Normalization

## Stato

**COMPLETATA**

Implementare:

```text
IngredientNormalizer
```

con:

```text
ingredient_normalization_v1
```

Il componente deve essere puro, deterministico e testabile.

Non deve ancora accedere al database.

Non deve ancora creare `product_ingredients`.

Non deve effettuare candidate generation.

---

# 22. Fase 5.3 — Canonical Candidate Generation

Implementare il motore che propone canonical ingredients possibili.

Input:

```text
normalized ingredient text
```

Candidate source:

```text
ingredients
ingredient_aliases
```

Metodi iniziali:

```text
exact canonical
exact alias
deterministic variants
conservative fuzzy matching
```

Output concettuale:

```text
ingredient_id
candidate_method
candidate_confidence
rationale
```

Nessun EFSA/scoring.

---

# 23. Fase 5.4 — Mapping Service

Integrare:

```text
label_extraction_items
→
IngredientNormalizer
→
product_ingredients
→
CandidateGenerator
→
mapping review
```

Responsabilità:

- materializzazione idempotente;
- persistenza normalized text;
- provenance;
- creazione candidate;
- creazione review quando necessaria;
- gestione mapping deterministici.

---

# 24. Fase 5.5 — Automatic Deterministic Resolution

Consentire auto-resolution esclusivamente per casi deterministicamente univoci.

Esempi:

```text
exact canonical unique
```

oppure:

```text
accepted alias exact unique
```

Fuzzy matching non deve inizialmente produrre auto-accept.

---

# 25. Fase 5.6 — Human Review API

Introdurre endpoint per:

```text
list pending reviews
review detail
accept
ambiguous
reject
manual mapping
```

La decisione deve essere transazionale e auditabile.

Il frontend Flutter rimane fuori scope.

---

# 26. Fase 5.7 — Alias Approval

Consentire opzionalmente al reviewer di trasformare un mapping verificato in un alias riutilizzabile.

L'operazione deve essere:

```text
esplicita
auditabile
versionabile
```

e non automatica.

---

# 27. Fase 5.8 — End-to-End Validation

Validare l'intero percorso utilizzando output reali della Fase 4.

Esempio:

```text
real ingredients image
        ↓
OpenAI extraction
        ↓
15 ingredient label_extraction_items
        ↓
normalization
        ↓
product_ingredients
        ↓
candidate generation
        ↓
deterministic mappings / pending reviews
        ↓
human review
        ↓
canonical ingredients
```

Verificare anche tramite query PostgreSQL la catena completa di provenance.

---

# 28. Test richiesti complessivamente

## Normalizer

```text
case folding
whitespace
Unicode
apostrofi
trattini
E-number
punctuation preservation
idempotenza
invalid input
```

## Candidate generator

```text
exact canonical
exact alias
language-aware alias
multiple candidates
no candidate
deprecated/non-accepted alias ignored
fuzzy candidate generation
```

## Mapping service

```text
ingredient extraction item → product ingredient
non ingredient item rejected
wrong product rejected
duplicate execution idempotent
provenance maintained
```

## Review

```text
pending
accepted
ambiguous
rejected
```

## Integrity

```text
duplicate extraction item rejected
duplicate pending review rejected
accepted with 0 selected rejected
accepted with >1 selected rejected
accepted with exactly 1 selected accepted
candidate only toward ingredients
```

## Migration

Ogni nuova migration dovrà verificare:

```text
upgrade
downgrade
re-upgrade
```

---

# 29. Criteri di chiusura Fase 5

La Fase 5 può essere considerata conclusa quando WYE è in grado di partire da veri:

```text
label_extraction_items
```

prodotti dalla Fase 4 e ottenere:

```text
normalized ingredient text
```

poi:

```text
canonical mapping candidate(s)
```

e infine uno dei risultati:

```text
accepted
ambiguous
rejected/unmapped
```

con completa provenance.

Deve essere possibile seguire la catena:

```text
product
→ product_ingredient
→ canonical ingredient
→ review
→ candidate
→ label_extraction_item
→ extraction_run
→ image
```

senza perdita del testo originale.

---

# 30. Fuori scope della Fase 5

La Fase 5 NON deve introdurre:

```text
EFSA ingestion
OpenFoodTox ingestion
scientific assessment ingestion
risk calculation
product scoring
nutrition scoring
personalized health recommendations
frontend Flutter
vector database obbligatorio
AI auto-approval
```

Questi aspetti appartengono alle fasi successive.

---

# 31. Roadmap aggiornata

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

Fase 4
Label Extraction Pipeline
✅ COMPLETATA E VALIDATA E2E

Fase 4.1
Benchmark extraction / schema improvements
⏳ OPZIONALE

Fase 5
Normalizzazione e Review Mapping
✅ COMPLETATA E VALIDATA E2E

Fase 5.1
Mapping Integrity & Schema Hardening
✅ COMPLETATA

Fase 5.2
Deterministic Ingredient Normalization
✅ COMPLETATA

Fase 5.3
Canonical Candidate Generation
✅ COMPLETATA

Fase 5.4
Mapping Service
✅ COMPLETATA

Fase 5.5
Automatic Deterministic Resolution
✅ COMPLETATA

Fase 5.6
Human Review API
✅ COMPLETATA

Fase 5.7
Alias Approval
✅ COMPLETATA

Fase 5.8
End-to-End Validation
✅ COMPLETATA E VALIDATA E2E

Fase 6
EFSA / OpenFoodTox ingestion
🚧 IN CORSO

Fase 7
Scientific scoring
⏳ FUTURA
```

---

# 32. Sintesi semplice

La Fase 4 permette a WYE di leggere:

```text
"Acido Citrico (E 330)"
```

da una fotografia.

La Fase 5 deve permettere a WYE di capire, in modo tracciabile e controllabile, che quella stringa corrisponde a uno specifico ingrediente presente nel proprio catalogo.

Il percorso sarà:

```text
"Acido Citrico (E 330)"
        ↓
normalizzazione
        ↓
"acido citrico (e330)"
        ↓
candidate generation
        ↓
Acido citrico
        ↓
review / deterministic resolution
        ↓
canonical ingredient WYE
```

senza ancora attribuire rischi, valutazioni scientifiche o score.

La Fase 5 costruisce quindi il ponte tra:

```text
ciò che è scritto sull'etichetta
```

e:

```text
le entità canoniche su cui WYE
potrà successivamente costruire
evidenza scientifica e scoring.
```
