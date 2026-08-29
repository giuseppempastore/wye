# WYE — Fase 6: Scientific Evidence Ingestion

## Stato

**Fase 6: IN CORSO**

Branch:

```text
ingredients_score
```

Alembic head corrente:

```text
0017_ingredient_mapping_history
```

Checkpoint implementativo corrente:

```text
Fase 6.1.0 — Scientific Ingestion Integrity Review             ✅ COMPLETATA
Fase 6.1.1 — Source Identity Hardening                         ✅ COMPLETATA
Fase 6.1.2 — Release Identity & Artifact Provenance            ✅ COMPLETATA
Fase 6.1.3 — Scientific Ingestion Run                          ✅ COMPLETATA
Fase 6.1.4 — Assessment & Finding Identity Hardening           ✅ COMPLETATA
Fase 6.1.5 — Substance Identity Hardening                      ✅ COMPLETATA
Fase 6.1.6 — Ingredient → Substance Integrity                  ✅ COMPLETATA
Fase 6.2   — Source-Agnostic Ingestion Core                    ✅ COMPLETATA
Fase 6.3.1 — Scientific Substance Resolution                   ✅ COMPLETATA
Fase 6.3.2 — Substance Resolution Review Workflow              ✅ COMPLETATA
Fase 6.3.3 — Substance Registry Materialization                ✅ COMPLETATA
Fase 6.3.4 — Controlled Substance Creation                     ✅ COMPLETATA
Fase 6.3.5 — Ingredient → Substance Mapping Workflow           ✅ COMPLETATA
Fase 6.3.6 — Final Validation & Mapping History                ✅ COMPLETATA
Fase 6.4   — EFSA Adapter                                      ⏳ PROSSIMA — NON INIZIATA
```

La Fase 6 nel suo complesso resta in corso. In particolare:

```text
scientific evidence != scientific scoring
```

La Fase 6.4 è il prossimo blocco e non fa parte di questo checkpoint.

Stato fasi precedenti:

```text
Fase 1   — Alembic e baseline                         ✅ COMPLETATA
Fase 2   — Scientific Data Model e provenance         ✅ COMPLETATA
Fase 2.1 — Data Integrity Hardening                   ✅ COMPLETATA
Fase 3   — Object Storage e acquisizione immagini     ✅ COMPLETATA
Fase 3.1 — Repository Hygiene                         ✅ COMPLETATA
Fase 4   — Label Extraction Pipeline                  ✅ COMPLETATA E VALIDATA E2E
Fase 5   — Normalizzazione e Review Mapping           ✅ COMPLETATA E VALIDATA E2E
Fase 6   — Scientific Evidence Ingestion              🚧 IN CORSO
Fase 7   — Scientific Scoring                         ⏳ FUTURA
```

La Fase 5 termina con la trasformazione:

```text
label_extraction_items
→ normalizzazione
→ candidate generation
→ product_ingredients
→ deterministic resolution / human review
→ canonical ingredients
```

La Fase 6 parte dalle entità canoniche scientifiche e introduce la gestione versionata e auditabile delle evidenze.

---

# 1. Obiettivo della Fase 6

La Fase 6 deve permettere a WYE di acquisire, conservare, normalizzare e rendere interrogabili evidenze scientifiche provenienti da fonti autorevoli.

La domanda a cui deve rispondere è:

```text
"Quali evidenze scientifiche e regolatorie
sono disponibili per questa sostanza?"
```

La Fase 6 NON deve ancora rispondere a:

```text
"Quanto è rischioso questo ingrediente?"
```

oppure:

```text
"Quale score deve ricevere il prodotto?"
```

Questi aspetti appartengono alla futura Fase 7.

---

# 2. Confine architetturale Fase 6 / Fase 7

Separazione obbligatoria:

```text
FASE 4
immagine
→ testo estratto

FASE 5
testo estratto
→ ingrediente canonico WYE

FASE 6
fonte scientifica
→ sostanza
→ assessment
→ findings normalizzati
→ provenance

FASE 7
evidenze scientifiche normalizzate
→ scoring model
→ ingredient score
→ product score
```

Principio fondamentale:

```text
scientific evidence
≠
scientific interpretation/scoring
```

La Fase 6 deve conservare i dati scientifici senza incorporare risk score hardcoded o giudizi non tracciabili.

---

# 3. Fonti iniziali previste

Le prime fonti previste sono:

```text
EFSA
OpenFoodTox
```

Non devono essere modellate con tabelle dedicate.

Devono essere configurate attraverso il modello generico:

```text
source
→ source_dataset
→ source_dataset_release
```

Gli adapter applicativi saranno invece source-specific.

Esempio concettuale:

```text
EFSA adapter
OpenFoodTox adapter
```

entrambi devono produrre dati compatibili con lo stesso modello scientifico interno.

---

# 4. Principio architetturale della pipeline

La pipeline target della Fase 6 è:

```text
external scientific source
        ↓
source
        ↓
dataset
        ↓
immutable dataset release
        ↓
raw scientific artifact
        ↓
source-specific parser
        ↓
ingestion run
        ↓
substance identity
        ↓
scientific assessment
        ↓
normalized findings
        ↓
provenance/versioning
```

L'acquisizione e il parsing devono essere separati.

Una stessa release/raw artifact deve poter essere rielaborata in futuro con una nuova versione del parser senza perdere il risultato precedente.

---

# 5. Modello scientifico già presente

Lo schema corrente contiene già:

```text
sources
source_datasets
source_dataset_releases

ingredients
ingredient_substances

substances
substance_identifiers

scientific_assessments
scientific_assessment_findings
```

Queste tabelle costituiscono la base della Fase 6.

---

# 6. `ingredients`

Gli `ingredients` rappresentano ciò che WYE riconosce e canonizza a partire dall'etichetta.

Esempio:

```text
Acido citrico
Benzoato di sodio
Lecitina di soia
```

Gli ingredienti NON devono essere usati direttamente come identità scientifica universale.

---

# 7. `substances`

Le `substances` rappresentano l'entità scientifica/regolatoria canonica.

Sono il target naturale delle evidenze scientifiche.

Un ingrediente può:

```text
rappresentare
contenere
derivare da
essere una miscela di
essere equivalente a
```

una o più sostanze.

---

# 8. `ingredient_substances`

Bridge N:M tra:

```text
ingredients
↔
substances
```

Relationship types già supportati:

```text
represents
contains
derived_from
mixture_component
equivalent_to
```

Mapping status già supportati:

```text
accepted
pending_review
ambiguous
rejected
legacy_unreviewed
```

Il modello N:M deve essere preservato perché deve poter rappresentare:

- ingrediente che rappresenta una singola sostanza;
- ingrediente multi-substance;
- mixture;
- derivato;
- componenti;
- equivalenze.

Per l'uso scientifico futuro devono essere considerati affidabili soltanto mapping con stato coerente e approvato.

---

# 9. `sources`

`sources` è il registry generico delle fonti scientifiche/regolatorie.

Non esiste e non deve essere introdotta una tabella dedicata del tipo:

```text
scientific_sources
```

La review read-only ha confermato però un gap importante:

```text
sources
```

non possiede ancora una stable machine-readable identity.

Attualmente non bisogna dipendere da:

```text
database ID hardcoded
source_name
URL
```

come identità logica permanente.

La Fase 6.1 dovrà quindi introdurre una stable key concettualmente equivalente a:

```text
source_key
```

Esempi futuri:

```text
efsa
openfoodtox
```

---

# 10. `source_datasets`

Un dataset è una collezione logica stabile appartenente a una source.

L'invariante già esistente:

```text
UNIQUE(source_id, dataset_key)
```

è una buona base.

Semantica:

```text
source
= organizzazione / sistema autore dei dati

dataset
= collezione o flusso logico stabile

release
= snapshot / versione specifica del dataset
```

---

# 11. `source_dataset_releases`

Le release rappresentano versioni o snapshot di un dataset.

Campi già disponibili includono:

```text
version_label
released_at
acquired_at
source_url
checksum
checksum_algorithm
format
release_status
license_text
```

Status correnti:

```text
declared
acquired
validated
superseded
rejected
```

La review read-only ha evidenziato che l'attuale modello non separa ancora in modo sufficientemente forte:

```text
external release identity
```

da:

```text
artifact content identity
```

Principio futuro:

```text
release concettuale
≠
file/raw artifact
```

Due release concettualmente diverse possono teoricamente avere contenuto byte-identico.

Un checksum del file non deve quindi diventare automaticamente l'identità della release.

---

# 12. Raw scientific artifact

La Fase 3 ha già introdotto:

```text
storage_objects
```

per object storage privato.

La Fase 6 dovrà riutilizzare tale infrastruttura.

La direzione architetturale preferita è:

```text
source_dataset_release
        ↓
scientific release artifact
        ↓
storage_object
```

L'entità intermedia dovrà poter rappresentare concetti quali:

```text
primary file
manifest
metadata
attachment
archive
other
```

Questo permette a una release di possedere più artifact senza introdurre logica source-specific nel database.

---

# 13. Ingestion run

La review Fase 6 ha confermato che manca completamente il concetto esplicito di:

```text
scientific ingestion run
```

Un ingestion run rappresenta:

```text
un tentativo concreto e versionato
di processare una specifica release
con uno specifico importer/parser
```

Dovrà conservare almeno concettualmente:

```text
release
importer name
importer version
source adapter version
acquisition version
parser version
normalization/schema version
started_at
completed_at
status
record counts
error summary
config/provenance
artifact manifest fingerprint
```

La stessa release deve poter essere processata più volte.

Esempio:

```text
release A
+ parser v1
→ ingestion run 1

release A
+ parser v2
→ ingestion run 2
```

Il secondo run NON deve sovrascrivere il primo.

---

# 14. Checksum semantics

I checksum devono avere semantica esplicita.

La review ha evidenziato che i checksum correnti di release e assessment sono troppo generici.

In futuro bisognerà distinguere almeno:

```text
raw artifact checksum
normalized assessment checksum
eventuale parser output checksum
```

Ogni checksum deve specificare:

```text
algorithm
value
what was hashed
```

Default futuro consigliato per nuovi artefatti:

```text
SHA-256
```

ma senza reinterpretare automaticamente checksum legacy di cui non sia nota la semantica.

---

# 15. `substance_identifiers`

Gli identificatori scientifici/regolatori possono includere:

```text
CAS
EC / EINECS
E-number
identifier source-specific
altri namespace
```

Lo schema corrente garantisce:

```text
UNIQUE(identifier_system, normalized_value)
```

La review ha evidenziato che `identifier_system` è ancora troppo libero per diventare un registry scientifico robusto.

La futura Fase 6 dovrà definire una strategia per:

```text
namespace
versione del namespace
normalizzazione
provenance
```

Non va però introdotta prematuramente logica specifica EFSA/OpenFoodTox nel DB.

---

# 16. Substance identity

La sostanza non deve essere deduplicata esclusivamente tramite nome.

La review ha evidenziato che:

```text
substances.normalized_name UNIQUE
```

può risultare insufficiente o troppo restrittivo come identità scientifica.

Problemi possibili:

```text
sinonimi
omonimi
forme chimiche differenti
record importati inizialmente separati
```

La Fase 6 dovrà preparare una futura gestione auditabile delle equivalenze/merge.

Principio:

```text
mai destructive merge silenzioso
```

Le decisioni di identità devono poter essere ricostruite.

Un vero merge engine automatico resta fuori scope della Fase 6.1 iniziale.

---

# 17. `scientific_assessments`

Gli assessment sono versionati e attualmente collegati a:

```text
substance
source_dataset_release
```

Contengono concetti quali:

```text
assessment_type
assessment_version
external_assessment_id
assessment_status
publication date
document reference
conclusion text
assessment_data JSONB
checksum
```

La review ha confermato alcuni gap importanti:

- identity insufficiente per re-import/reprocessing;
- checksum semanticamente ambiguo;
- assenza di ingestion run;
- collegamento diretto a una sola substance;
- status scientifico e status WYE potenzialmente mescolati.

La Fase 6 dovrà permettere di conservare assessment storici prodotti da run differenti senza aggiornamenti distruttivi.

---

# 18. Assessment identity

Serve una natural identity idempotente per impedire duplicazioni durante un import.

Non è ancora approvata una singola chiave definitiva.

La direzione consigliata è distinguere:

```text
source-native identity
external assessment id/version
source record key
ingestion run identity
normalized content fingerprint
```

Un assessment corretto o ripubblicato in una release successiva deve poter essere conservato come nuova materializzazione storica.

---

# 19. Assessment multi-substance

Lo schema corrente collega ogni assessment direttamente a una sola `substance`.

La review ha evidenziato che questo potrebbe non essere sufficiente.

In futuro potrebbe essere necessario:

```text
scientific_assessment
        ↕
scientific_assessment_substances
        ↕
substances
```

Non è ancora deciso se questa modifica debba entrare subito nella Fase 6.1 o essere introdotta successivamente dopo i primi dataset reali.

Principio:

```text
non modellare prematuramente una cardinalità 1:1
se la fonte scientifica può descrivere più sostanze
```

---

# 20. Assessment status

Status correnti:

```text
pending_review
published
superseded
withdrawn
rejected
```

La review ha evidenziato che possono rappresentare concetti diversi.

Devono essere distinti almeno concettualmente:

```text
source scientific status
```

da:

```text
WYE review status
```

da:

```text
ingestion run status
```

Esempio:

```text
published
```

può descrivere lo stato scientifico presso la fonte.

```text
pending_review
```

può invece descrivere uno stato interno WYE.

Questi concetti non devono essere mescolati senza semantica esplicita.

---

# 21. `assessment_type`

`assessment_type` deve rimanere source-agnostic ed estensibile.

Non deve essere costruito come enum rigido basato sui primi documenti EFSA osservati.

Possibili categorie concettuali:

```text
hazard_characterization
exposure_assessment
risk_characterization
regulatory_opinion
reference_value
classification
other
```

Il vocabolario definitivo deve essere introdotto solo quando sufficientemente stabile.

---

# 22. `scientific_assessment_findings`

I findings rappresentano singoli risultati o conclusioni normalizzate di un assessment.

Il nucleo corrente include concetti quali:

```text
endpoint
numeric value
text value
unit
population context
evidence type
conclusion text
source locator
```

La review ha confermato che manca una identity idempotente.

Un re-import potrebbe quindi duplicare findings.

La futura identity dovrà considerare:

```text
source-native finding key
source locator
source ordinal
deterministic fingerprint
```

senza deduplicare aggressivamente risultati scientificamente distinti che condividono lo stesso valore numerico.

---

# 23. Minimal normalized finding core

La Fase 6 non deve tentare di creare un'ontologia scientifica universale.

Il nucleo normalizzato deve rimanere minimo.

Possibili campi normalizzati:

```text
finding_type
endpoint
value_numeric
value_text
unit
population_context
evidence_type
conclusion_text
source_locator
source_ordinal
source_finding_key
```

Deve inoltre essere possibile conservare:

```text
raw/source-specific payload JSONB
```

Principio:

```text
normalizzare ciò che comprendiamo
senza perdere ciò che non abbiamo ancora modellato
```

---

# 24. Raw → normalized provenance

La catena completa futura deve essere ricostruibile.

Target:

```text
scientific_assessment_finding
        ↓
scientific_assessment
        ↓
scientific_ingestion_run
        ↓
source_dataset_release
        ↓
scientific release artifact
        ↓
storage_object
        ↓
source_dataset
        ↓
source
```

E dal lato WYE:

```text
ingredient
        ↓
ingredient_substance
        ↓
substance
        ↓
scientific assessment relation
        ↓
scientific_assessment
        ↓
finding
```

L'obiettivo è poter rispondere in futuro a domande come:

```text
"Da quale fonte deriva questo dato?"

"Da quale release?"

"Da quale file?"

"Con quale parser?"

"Con quale versione?"

"Quale record raw ha prodotto questo finding?"
```

---

# 25. Record rimossi/corretti tra release

Scenario:

```text
Release A
contiene assessment X

Release B
non contiene assessment X
```

WYE NON deve automaticamente:

```text
cancellare X
```

né assumere:

```text
assenza in B = withdrawn
```

L'assenza può dipendere da:

```text
diversa composizione del dataset
correzione
filtro
split del dataset
cambio del feed
```

Principio:

```text
ogni assessment rimane storicamente scoped
alla release/run che lo ha prodotto
```

`withdrawn` deve richiedere evidenza esplicita o una decisione auditabile.

---

# 26. Release supersession/current semantics

La review ha proposto una possibile gestione append-only delle release promosse/current.

La decisione definitiva è ancora aperta.

Principi già approvati:

- nessuna cancellazione distruttiva;
- una release precedente deve rimanere interrogabile;
- una release nuova non deve cancellare automaticamente la precedente;
- un rollback operativo deve poter preservare la storia;
- evitare booleani fragili tipo `is_current` se il concetto può essere modellato in modo più auditabile.

Una eventuale tabella di release promotions resta da valutare dopo aver definito meglio il comportamento reale delle fonti iniziali.

---

# 27. Idempotenza

Ogni livello della pipeline deve avere un'identità coerente.

Target concettuale:

```text
source
→ stable source_key

dataset
→ source + dataset_key

release
→ dataset + external release identity

artifact
→ release + artifact identity

ingestion run
→ explicit run/idempotency identity

substance identifier
→ namespace + normalized identifier

assessment
→ ingestion/source record identity

finding
→ assessment + source finding identity
```

La Fase 6 deve impedire:

```text
duplicazioni silenziose
```

ma senza confondere:

```text
same scientific concept
```

con:

```text
same import execution
```

---

# 28. Concorrenza

Devono essere considerati scenari con worker concorrenti.

Esempi:

```text
due worker registrano la stessa release
due worker acquisiscono lo stesso artifact
due ingestion run usano la stessa idempotency key
due importer persistono lo stesso assessment
due worker persistono lo stesso finding
due substance tentano lo stesso identifier
```

Strategia:

```text
DB constraint
+
transaction
+
application conflict handling
```

Non affidarsi esclusivamente a check applicativi pre-insert.

---

# 29. Parser e importer versioning

Distinzioni obbligatorie:

```text
source adapter version
acquisition version
parser version
normalization/schema version
```

Significato:

```text
source adapter version
= logica di integrazione con la fonte

acquisition version
= logica/config/protocollo di acquisizione artifact

parser version
= raw → parsed records

normalization/schema version
= parsed records → modello WYE
```

Una nuova versione del parser applicata allo stesso artifact deve poter produrre un nuovo run auditabile.

---

# 30. Legacy scientific/scoring code

Esistono componenti legacy:

```text
backend/app/services/scoring.py
backend/app/data/ingredients.py
ingredient_evidence
ingredient_risk_profiles
product_scores
cosmetic_ingredient_assessment
```

Questi componenti:

- NON devono essere usati come modello scientifico primario della Fase 6;
- NON devono guidare il nuovo schema;
- NON devono essere automaticamente migrati;
- NON devono essere refactorati durante le prime sottofasi della Fase 6.

Potranno eventualmente diventare:

```text
compatibility projection
migration source
legacy layer
Fase 7 component
```

solo dopo decisione esplicita.

---

# 31. Review read-only completate

## Fase 6.0 — Scientific Data Model Review

**COMPLETATA**

Obiettivo:

comprendere il modello già presente e verificare se fosse sufficiente per iniziare ingestion reale.

Risultato:

```text
buona base
ma ulteriori invarianti necessarie
```

---

## Fase 6.1.0 — Scientific Ingestion Integrity & Release Hardening Review

**COMPLETATA — READ ONLY**

Nessun codice o DB modificato.

Gap principali confermati:

1. stable source key assente;
2. identità release e artifact non sufficientemente separate;
3. ingestion run assente;
4. checksum semanticamente ambigui;
5. assessment identity insufficiente per reprocessing;
6. finding identity assente;
7. source scientific status e WYE status non chiaramente separati;
8. raw artifact non collegato alla release;
9. substance identity merge non auditabile;
10. `ingredient_substances` necessita ulteriori invarianti.

---

# 32. Strategia di implementazione

La Fase 6.1 NON verrà implementata come una singola migration enorme.

Si procede tramite checkpoint piccoli, isolati e testabili.

Roadmap approvata:

```text
Fase 6.1.0
Read-only Scientific Ingestion Integrity Review
✅ COMPLETATA

Fase 6.1.1
Source Identity Hardening
✅ COMPLETATA

Fase 6.1.2
Release Identity & Artifact Provenance
✅ COMPLETATA

Fase 6.1.3
Scientific Ingestion Run
✅ COMPLETATA

Fase 6.1.4
Assessment & Finding Identity Hardening
✅ COMPLETATA

Fase 6.1.5
Substance Identity Hardening
✅ COMPLETATA

Fase 6.1.6
Ingredient → Substance Integrity
✅ COMPLETATA
```

---

# 33. Fase 6.1.1 — Source Identity Hardening

Prima implementazione prevista.

Obiettivo:

introdurre una stable machine-readable identity per:

```text
sources
```

Concetto:

```text
source_key
```

Requisiti:

```text
stable
unique
NOT NULL finale
machine-readable
indipendente da display name
indipendente da URL
indipendente da DB ID
```

Esempi futuri:

```text
efsa
openfoodtox
```

La migration deve essere:

```text
piccola
isolata
reversibile
testata su PostgreSQL reale
```

Non deve introdurre altro hardening scientifico.

---

# 34. Fase 6.1.2 — Release Identity & Artifact Provenance

Obiettivo futuro:

separare:

```text
release identity
```

da:

```text
raw artifact identity
```

e costruire la catena:

```text
source_dataset_release
→ scientific release artifact
→ storage_object
```

Temi principali:

```text
external_release_key
artifact role
raw checksum
storage provenance
release lifecycle
```

Una eventuale strategia di release promotion/current verrà valutata separatamente.

---

# 35. Fase 6.1.3 — Scientific Ingestion Run

Obiettivo:

introdurre il concetto esplicito di esecuzione dell'ingestion.

Target:

```text
release
+ artifacts
+ importer/parser versions
→ ingestion run
```

Requisiti:

```text
versioned
auditable
idempotent
retry-safe
concurrency-safe
```

Nessuna sorgente reale sarà ancora obbligatoria per validare il modello.

Fixture offline PostgreSQL saranno sufficienti.

---

# 36. Fase 6.1.4 — Assessment & Finding Identity Hardening

Obiettivo:

rendere assessment e findings:

```text
idempotenti
versionabili
re-processabili
auditabili
```

Temi:

```text
source record identity
external assessment identity
normalized checksum semantics
finding identity
raw payload preservation
parser provenance
```

La modifica multi-substance degli assessment verrà rivalutata in questo checkpoint.

---

# 37. Fase 6.1.5 — Substance Identity Hardening

Obiettivo:

preparare un registry scientifico affidabile.

Temi:

```text
identifier namespaces
identifier normalization
duplicate identifier conflict handling
substance identity resolution
auditabile merge/equivalence
```

Non implementare un merge automatico.

---

# 38. Fase 6.1.6 — Ingredient → Substance Integrity

Obiettivo:

blindare:

```text
ingredient_substances
```

prima del workflow applicativo della Fase 6.3.

Temi:

```text
mapping status coherence
review metadata
temporal constraints
dataset/run provenance
accepted-only scientific usage
```

---

# 39. Fase 6.2 — Source-Agnostic Ingestion Core

## Stato

**COMPLETATA**

Dopo il completamento della Fase 6.1.

Obiettivo:

implementare l'infrastruttura applicativa generica per ingestion.

Componenti previsti:

```text
adapter interface
artifact manifest
parser result models
ingestion service
repository layer
idempotency handling
offline fixture provider
```

Nessuna dipendenza obbligatoria da EFSA/OpenFoodTox reali.

---

# 40. Fase 6.3 — Substance Registry & Mapping Workflow

## Stato

**COMPLETATA — FASE 6.3.1 → 6.3.6 COMPLETATE**

Obiettivo:

gestire:

```text
imported identifiers
→ substance identity
→ deduplication/review
→ ingredient_substances
```

Principio:

```text
mapping scientificamente ambiguo
→ review
```

Non creare automaticamente equivalenze scientifiche senza evidenza.

---

# 41. Fase 6.4 — EFSA Adapter

## Stato

**PROSSIMA — NON INIZIATA**

Solo dopo hardening e core source-agnostic.

Pipeline prevista:

```text
EFSA acquisition
→ immutable artifact
→ versioned EFSA parser
→ source-agnostic ingestion models
→ substances
→ assessments
→ findings
```

L'acquisition deve essere separata dal parser.

La persistenza non deve contenere logica EFSA-specifica non necessaria.

---

# 42. Fase 6.5 — OpenFoodTox Adapter

Adapter separato.

Pipeline equivalente:

```text
OpenFoodTox acquisition
→ immutable artifact
→ versioned parser
→ source-agnostic ingestion models
→ substances
→ assessments
→ findings
```

Il modello interno deve rimanere comune.

---

# 43. Fase 6.6 — Cross-source Validation

Validazione finale della Fase 6.

Dovrà verificare almeno:

```text
release A
release B
supersession/version history
reprocessing
same artifact / different parser
assessment identity
finding identity
substance identity
cross-source evidence
provenance traversal
idempotency
concurrency
rollback
migration lifecycle
```

Al termine sarà prodotto un documento separato:

```text
Checkpoints/fase_6_validazione_end_to_end.md
```

---

# 44. Test strategy

Tutte le migration e le invarianti scientifiche devono essere validate su:

```text
PostgreSQL reale
```

Non soltanto tramite mock.

Categorie di test previste:

## Constraint tests

```text
unique identity
foreign keys
status coherence
temporal constraints
checksum pairing
accepted/review invariants
```

## Idempotency tests

```text
same source
same dataset
same release identity
same artifact
same run key
same assessment record
same finding record
same identifier
```

## Concurrency tests

```text
duplicate release creation
duplicate artifact registration
same ingestion run
assessment race
finding race
identifier race
```

## Migration lifecycle

Ogni migration deve verificare:

```text
upgrade
downgrade
re-upgrade
```

su database temporaneo dedicato.

## Provenance tests

Deve essere possibile ricostruire:

```text
finding
→ assessment
→ ingestion run
→ release
→ artifact
→ storage object
→ dataset
→ source
```

---

# 45. Principi di migration

Ogni sottofase deve rispettare:

```text
migration isolata
schema delta minimo
upgrade sicuro
downgrade definito
backfill esplicito
nessun dato scientifico inventato
nessun destructive rewrite silenzioso
```

Le migration non devono assumere che metadata legacy ambiguamente nominati abbiano una semantica che non è stata verificata.

---

# 46. Principi di provenance

Ogni dato scientifico importante deve poter rispondere a:

```text
da dove proviene?
quando è stato acquisito?
quale release?
quale artifact?
quale checksum?
quale parser?
quale parser version?
quale normalization version?
quale record source-native?
quale decisione umana?
```

La provenance deve essere conservata per consentire:

```text
audit
debug
reprocessing
scientific reproducibility
future scoring explainability
```

---

# 47. Principi di conservazione dello storico

Non effettuare:

```text
overwrite distruttivo
delete automatico di assessment precedenti
remapping retroattivo silenzioso
merge distruttivo di substances
```

Preferire:

```text
append
version
supersede
review
audit
```

quando scientificamente e tecnicamente appropriato.

---

# 48. Fuori scope della Fase 6

La Fase 6 NON deve introdurre:

```text
ingredient risk score
product risk score
nutrition score
personalized health recommendations
AI-generated scientific conclusions
frontend Flutter scientifico
vector database obbligatorio
embedding-based scientific truth
AI auto-approval
hardcoded EFSA score
hardcoded OpenFoodTox score
```

L'AI potrà eventualmente assistere in attività future, ma non sarà l'autorità scientifica canonica.

---

# 49. Criteri di chiusura della Fase 6

La Fase 6 potrà essere considerata completata quando WYE sarà in grado di:

1. identificare stabilmente una source;
2. identificare dataset e release;
3. conservare raw artifact immutabili e verificabili;
4. processarli attraverso ingestion run versionati;
5. identificare e collegare substances;
6. importare scientific assessments;
7. importare findings normalizzati;
8. conservare raw/source-specific payload;
9. garantire idempotenza;
10. gestire reprocessing;
11. gestire release multiple;
12. preservare storico;
13. ricostruire provenance completa;
14. gestire concorrenza senza duplicazioni silenziose;
15. integrare almeno EFSA e OpenFoodTox tramite adapter separati;
16. validare tutto end-to-end su PostgreSQL reale.

Nessuno scoring è necessario per dichiarare completata la Fase 6.

---

# 50. Sintesi semplice

La Fase 5 permette a WYE di capire:

```text
"Acido Citrico (E330)"
        ↓
Acido citrico
```

La Fase 6 deve permettere a WYE di collegare quell'entità al mondo scientifico.

Esempio concettuale:

```text
Acido citrico
        ↓
substance scientifica
        ↓
EFSA / OpenFoodTox
        ↓
specifica release
        ↓
specifico file acquisito
        ↓
specifico parser versionato
        ↓
assessment
        ↓
findings scientifici
```

con la possibilità di dimostrare sempre:

```text
chi ha pubblicato il dato,
quale versione è stata usata,
quale file è stato acquisito,
come è stato interpretato,
e quale record scientifico è stato prodotto.
```

La Fase 6 costruisce quindi il ponte tra:

```text
ingrediente canonico WYE
```

e:

```text
evidenza scientifica verificabile e versionata
```

senza ancora trasformarla in uno score.
