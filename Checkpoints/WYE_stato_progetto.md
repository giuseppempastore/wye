# WYE — Stato del progetto

## Baseline corrente

```text
branch: ingredients_score
HEAD: a16c0103e648479b81fa2ded8f64377323ebfeb4
origin/ingredients_score: 48a0681e7e928bec47441d468c86f20784d00ea5
Alembic repository head: 0021_scientific_evaluation_publication
local database wye: 0017_ingredient_mapping_history
```

Il database locale deve essere aggiornato separatamente tramite backup, upgrade a
`0018` e validazione. Le Fasi 7.6.2A e 7.6.2B non aggiornano il database locale.

## Avanzamento

```text
Fase 1      COMPLETATA
Fase 2      COMPLETATA
Fase 2.1    COMPLETATA
Fase 3      COMPLETATA
Fase 3.1    COMPLETATA
Fase 4      COMPLETATA + E2E
Fase 5      COMPLETATA + E2E
Fase 6      COMPLETATA
Fase 7.0    COMPLETATA — Architecture & Requirements Review
Fase 7.0.1  COMPLETATA — Architecture Specification & Phase 7.0 Freeze
Fase 7.1    COMPLETATA — Logical protocol / snapshot / execution model
Fase 7.2    COMPLETATA — Evidence eligibility & selection semantics
Fase 7.3    COMPLETATA — Endpoint synthesis / substance assessment semantics
Fase 7.4    COMPLETATA — Substance-to-ingredient projection semantics
Fase 7.5    COMPLETATA — Exposure readiness / product assessment semantics
Fase 7.6    COMPLETATA — Persistence, explainability & historical replay design
Fase 7.6.1  COMPLETATA — Canonicalization/schema/publication freeze
Fase 7.6.2A IMPLEMENTATA E VALIDATA — Scientific evaluation persistence foundation
Fase 7.6.2B-1 COMPLETATA — Scientific evidence snapshots design/freeze
Fase 7.6.2B-2 IMPLEMENTED + VALIDATED
Fase 7.6.3A COMPLETED + COMMITTED
Fase 7.6.3B COMPLETED + COMMITTED
Fase 7.6.4A-1 DESIGN FROZEN — READY FOR IMPLEMENTATION
Fase 7.6.4A-1B AUTHORITY MULTIPLICITY AMENDMENT FROZEN
Fase 7.6.4A-2 COMPLETED + COMMITTED
Fase 7.6.4B-1  DESIGN FROZEN
Fase 7.6.4B-1B REPLAY SEMANTICS AMENDMENT FROZEN
Fase 7.6.4B-2  COMPLETED + COMMITTED
Fase 7.6.4C    COMPLETED + COMMITTED
Fase 7.7.1A   TECHNICAL CONTRACT FROZEN
Fase 7.7.1B   CANDIDATE POLICY FROZEN
Fase 7.7.1C   SCIENTIFIC REVIEW PACKAGE COMPLETED
Fase 7.7.2    COMPLETED + COMMITTED
Fase 7.7.3    HANDOFF READY — HUMAN REVIEW REQUIRED
```

## Capacità consolidate

WYE conserva e collega:

```text
product
→ extraction item
→ accepted canonical ingredient
→ accepted temporal ingredient-substance mapping
→ active substance and verified identifier
→ scientific assessment and finding
→ ingestion run and immutable artifact
→ release
→ dataset
→ source
```

La Fase 6 ha consolidato acquisizione reale EFSA QPS e OpenFoodTox, identity
resolution, provenance, reprocessing, multi-provider coexistence, batch,
checkpoint/resume, crash recovery, concurrency e storico.

## Fase 7.0.1

La progettazione iniziale dello scoring è congelata nei documenti:

- `Checkpoints/WYE_PHASE_7.md`;
- `WYE_SCORING_SEMANTICS.md`;
- `WYE_SCORING_PROTOCOL.md`.

Decisioni principali:

```text
evidence synthesis / hazard profile != risk estimate != generic health score

first protocol:
endpoint-specific evidence synthesis
+ multidimensional substance hazard profile

numeric score for first protocol:
not scientifically justified
```

Il rischio quantitativo di prodotto non è computabile con i dati attuali perché
mancano in modo generale concentrazione, dose/amount, frequenza, durata, route,
target population e condizioni di preparazione/uso.

## Confine legacy

Il simple scoring MVP, il catalogo/pesi hardcoded, gli score placeholder e le
tabelle/campi legacy di scoring sono classificati:

```text
legacy / excluded from Phase 7 scientific scoring
```

Non sono stati modificati o reinterpretati dalla Fase 7.0.1.

## Fase 7.1

Il modello logico versionato è definito in:

- `WYE_SCORING_EXECUTION_MODEL.md`.

Sono congelati a livello logico:

```text
scientific protocol family
immutable published protocol version
canonical protocol representation and digest
hybrid evidence snapshot: query definition + resolved membership
target identity snapshot
evidence selection decision contract
scientific evaluation execution
NORMAL / REPLAY / COUNTERFACTUAL / REFRESH
non-scalar result and result components
machine-readable explanation trace
determinism, idempotency and failure semantics
```

La review di compatibilità ha confermato che il layer Fase 6 fornisce provenance,
artifact checksum, versioni di ingestion/parser/normalizzazione, finding
fingerprint e mapping temporali utili allo snapshot. Restano requisiti futuri la
membership congelata completa, il target identity freeze, il lifecycle storico
della composizione prodotto e la persistence di protocollo, execution, decisioni,
risultati e trace.

La Fase 7.1 non definisce criteri scientifici concreti, endpoint synthesis,
formule, pesi, threshold, score numerici o runtime.

## Fase 7.2

Il contratto semantico del futuro selector è definito in:

- `WYE_EVIDENCE_SELECTION.md`.

Sono formalizzati:

```text
finding as normal atomic candidate; assessment as context
availability != eligibility != relevance != quality
eligibility and applicability dimension states
binary inclusion decision + deferred resolution state
versioned hybrid reason-code vocabulary
assessment lifecycle and time semantics
release + normalized ingestion representation
duplicate and dependency identities
endpoint/population/route/duration/value readiness
QPS and OpenFoodTox separate evidence channels
comparison groups without conflict synthesis
canonical decision and selection digests
```

La Fase 7.2 non implementa il selector e non definisce synthesis, hazard profile,
ingredient/product aggregation, formule, pesi, threshold o score numerici.

## Fase 7.3

Il contratto semantico della futura synthesis è definito in:

- `WYE_EVIDENCE_SYNTHESIS.md`.

Sono formalizzati:

```text
evidence line as dependency-aware synthesis input
comparison groups and endpoint semantic identity requirements
non-numeric endpoint synthesis states
agreement, discordance and true-conflict semantics
quality, relevance, sufficiency and coverage profiles
typed uncertainty propagation and confidence representation
endpoint synthesis and multidimensional substance hazard profile
QPS regulatory context separated from OpenFoodTox toxicology
cross-source and dependency-aware synthesis
canonical synthesis trace and deterministic digests
```

La Fase 7.3 non implementa runtime synthesis o hazard engine. Endpoint mappings,
direction-of-effect, concrete quality/sufficiency/confidence rules and hazard
interpretation restano soggetti a dati normalizzati e review scientifica esterna.

## Fase 7.4

Il contratto semantico della futura ingredient projection è definito in:

- `WYE_INGREDIENT_PROJECTION.md`.

Sono formalizzati:

```text
current mapping model and 0017 history audit
relationship-aware represents/equivalent_to/contains/mixture_component/derived_from semantics
mapping snapshot and inclusive as_of validity
direct, qualified, qualitative, blocked and unresolved projection states
ingredient_scientific_projection as a non-scalar substance-entry collection
projected/qualified/blocked dimensions
additive projection uncertainty and confidence constraints
ambiguous/rejected/absent mapping behavior
composition readiness without inferred quantity
separate QPS regulatory-context association
canonical trace and deterministic mapping/projection digests
```

La Fase 7.4 non implementa runtime projection, ingredient/product score,
cross-substance aggregation, exposure o risk. Form equivalence, composition,
mixture, residual-presence e confidence rules restano soggetti a data model e
review scientifica esterna.

## Fase 7.5

Il contratto semantico di exposure readiness e product assessment è definito in:

- `WYE_PRODUCT_ASSESSMENT.md`.

Sono formalizzati:

```text
current product/composition/extraction model audit
product_composition_snapshot and exposure_scenario envelopes
composition, unit/basis and exposure readiness states
no-silent-default and scenario-provenance policy
explicit risk-computability gate and risk_not_computable result
non-scalar product_scientific_assessment
scenario-specific outputs without ingredient/substance aggregation
separate hazard/projection/composition/exposure/reference uncertainty
hybrid reason codes, canonical trace and deterministic digests
```

Il DB locale contiene dieci prodotti, 27 product ingredients tutti
`legacy_unreviewed`, cinque nutrition facts e nessun image/document/extraction
record. Quantità ingrediente/sostanza, serving canonico storico, actual intake,
frequenza, durata, popolazione e preparation/use state non sono generalmente
disponibili. Il product risk resta quindi non computabile in generale.

La Fase 7.5 non implementa runtime exposure/risk, reference-point comparison,
product score, formule, pesi, threshold o output numerici.

## Fase 7.6

Il contratto di persistence, explainability e historical replay è definito in:

- `WYE_SCORING_PERSISTENCE.md`.

Sono formalizzati artifact canonici content-addressed, query projections
ricostruibili, lifecycle separati di execution/attempt, publication atomica su
DB e object storage, governance append-only, replay verifier, engine
compatibility, trace machine-readable, digest DAG non circolare, retention,
privacy, concurrency e migration decomposition.

La decisione di migration è `B`: il modello semantico è stabile, ma una migration
richiede prima il freeze tecnico di canonical JSON/decimal/time fixtures,
artifact envelope, schema e vincoli, publication/reconciliation, retention
dell'engine, privacy e access pattern. Nessuna struttura Phase 7 è ancora
presente nel DB.

## Fase 7.6.1

Il freeze tecnico implementabile è definito in:

- `WYE_SCORING_SCHEMA_FREEZE.md`.

Sono congelati `wye-c14n-json-v1`, SHA-256/BYTEA, canonical decimal/date/time,
artifact envelope e placement, naming e schema logico colonna per colonna,
vincoli/trigger/FK/index, execution identity, publication transaction e failure
recovery, workload, privacy, engine/replay levels, retention e migration slices.

La decisione finale è:

```text
READY FOR MIGRATION IMPLEMENTATION
```

Non restano blocker tecnici per la foundation `0019`; i prerequisiti relativi a
runtime artifact, object reconciliation, dati personali e regole scientifiche
sono esplicitamente differiti alle slice che li utilizzano.

## Fase 7.6.2A

La foundation autorizzata è implementata e validata nella revision:

```text
0019_scientific_evaluation_foundation
down_revision: 0018_scientific_batch_recovery
```

Sono create esclusivamente le cinque tabelle per artifact/location,
protocol/version e governance events, con PK/FK `RESTRICT`, CHECK, UNIQUE,
indici, trigger di immutabilità/append-only, lifecycle governato, collision
preflight e downgrade rifiutato quando esiste storia canonica. La colonna
metadata `alembic_version.version_num` viene ampliata a `VARCHAR(64)` per
contenere il revision ID congelato.

I test PostgreSQL dedicati validano fresh chain, `0018 → 0019`, downgrade vuoto
e protetto, constraint, concurrency, trigger e isolamento legacy. Non sono
implementati serializer/runtime persistence, snapshot, execution, result,
trace, replay o motori scientifici.

## Fase 7.6.2B-1

Il contratto persistence di Scientific Evidence Snapshots è congelato in
`WYE_SCORING_SCHEMA_FREEZE.md`.

```text
DESIGN FROZEN — READY FOR MIGRATION IMPLEMENTATION
target revision: 0020_scientific_evidence_snapshots
```

Lo snapshot congela il candidate universe tecnico disponibile a uno specifico
`as_of`/cutoff e snapshot-policy version. Il finding è il membro atomico normale;
l'assessment è contesto obbligatorio e diventa membro soltanto per record
assessment-level realmente atomici. Query, member payload e manifest sono
artifact canonici; il digest del manifest è l'identità scientifica dello
snapshot. Mapping state, target identity, eligibility/selection, synthesis e
result restano separati.

Sono congelati lifecycle `building -> sealed`, immutabilità post-seal, FK
`RESTRICT`, provenance completa tramite run/release/artifact manifest,
canonical ordering, idempotenza/concurrency, governance append-only,
preflight, downgrade only-when-empty e piano test 0020. Duplicate reingestion e
dependency non vengono trasformate in deduplicazione scientifica dal layer
snapshot.

## Fase 7.6.2B-2

La revision `0020_scientific_evidence_snapshots` è implementata e validata.
Introduce soltanto snapshot/membership persistence, sealing e
immutabilità, artifact binding, governance snapshot, preflight e downgrade
fail-safe. Il repository Alembic head è 0020; il database locale resta a
`0017_ingredient_mapping_history`.

Al termine della 7.6.2B serializer, artifact writer e snapshot
repository/finalizer non erano implementati; sono stati aggiunti nei successivi
checkpoint 7.6.3A/7.6.3B. Execution e replay runtime restano non implementati.
Non sono stati introdotti motori scientifici, formule, pesi,
threshold o score numerici; lo scoring legacy resta isolato.

## Fase 7.6.3A

`wye-c14n-json-v1` e il scientific artifact writer inline sono implementati,
validati e committed. Il serializer applica NFC, UTF-8, ordinamento key per
byte, escaping canonico, signed 64-bit integer e rifiuto dei binary float e dei
tipi Python non normalizzati. L'allowlist runtime copre `protocol_definition/1`,
`protocol_review/1` e i tre artifact snapshot v1.

Il writer calcola internamente SHA-256, inserisce o riusa l'identità canonica,
verifica metadata/cache/byte autoritativi, crea o riusa una location inline
verified e lascia commit/rollback al chiamante. Retry e concorrenza convergono
sulla stessa artifact/location identity; mismatch o bytes non dimostrabili
producono errori espliciti.

## Fase 7.6.3B

Repository, typed request model, deterministic builder e finalizer degli evidence
snapshot sono `COMPLETED + COMMITTED` nel commit
`f775e0e03a4cce348afc07c052d5a72a7c8568c1`. Il runtime riceve
membership esplicita, risolve la provenance Phase 6, materializza query/member/
manifest tramite il writer 7.6.3A, assegna l'ordine canonico e sigilla nello
stesso caller-owned transaction. Snapshot vuoti, retry, builder concorrenti,
historical status preservation e le due direzioni della race seal/mutation sono
coperti da test PostgreSQL reali.

`status_as_of` deriva dall'unico lifecycle assessment autorevole disponibile,
`scientific_assessments.assessment_status`; il release status è congelato
separatamente nella provenance e non viene simulato uno status finding assente
dallo schema. Mapping state, eligibility/selection, scoring execution,
execution/result persistence, replay/reproduce/recalculate e motori scientifici
restano non implementati. L'upgrade del database locale resta un task operativo
separato.

## Fase 7.6.4A-1

Il mapping state e il canonical non-protocol execution input sono congelati in
`WYE_MAPPING_EXECUTION_INPUT_FREEZE.md`. V1 supporta soltanto target
`substance` e `ingredient`; `product` resta subordinato a un successivo freeze
di composition/scenario storicamente riproducibile. Il mapping ingredient è
autorevole soltanto quando accept, bridge e materialization sono controllati,
visibili a `as_of` ed efficaci nel giorno UTC inclusivo. Stati legacy,
ambigui/pending/rejected/deferred restano provenance e non diventano membri.

Il freeze definisce gli artifact `scientific_evaluation_target/1`,
`scientific_mapping_state_member/1`,
`scientific_mapping_state_manifest/1` e `scientific_evaluation_input/1`.
`input_digest` lega target e mapping-state root; evidence snapshot, protocollo,
mode e configuration restano root separati del futuro
`semantic_execution_digest`. Il substrate 0019/0020 è sufficiente al runtime
7.6.4A; la futura 0021 dovrà includere FK esplicite ai root canonici.

Stato:

```text
DESIGN FROZEN — READY FOR IMPLEMENTATION
```

## Fase 7.6.4A-1B

L'emendamento in `WYE_MAPPING_EXECUTION_INPUT_FREEZE.md` congela la cardinalità
reale Phase 6: un bridge `ingredient_substances` produce un mapping member e può
avere zero o più authority chain; un member incluso richiede almeno una chain
accept/materialization valida e contiene tutte quelle visibili a `as_of` in
ordine canonico. `applied` e `already_current` confermano lo stesso bridge senza
precedence o duplicazione scientifica. Una adozione controllata
`already_current` può rendere autorevole un bridge accepted pre-workflow solo
dal relativo viewpoint registrato, senza retroattività.

Sono congelati anche `non_member_observations`, identity/payload/digest, closed
reason vocabulary, order, impact e decision table degli stati. Una violazione
storica invalida produce `history_unavailable`; una candidate uncertainty con
subset autorevole non vuoto produce `partially_resolved`; senza subset produce
`history_unavailable`; nessun blocker produce `resolved` o `empty` secondo il
member count.

```text
Phase 7.6.4A-1B:
AUTHORITY MULTIPLICITY AMENDMENT FROZEN

Phase 7.6.4A-2:
COMPLETED + COMMITTED
```

## Prossimo gate

La Phase 7.6.4A è completata e persistita in Git nel commit
`a16c0103e648479b81fa2ded8f64377323ebfeb4`. Il runtime produce target, mapping
member/manifest e canonical evaluation input tramite l'artifact writer 0019,
senza nuove tabelle.

La Phase 7.6.4B-1 congela in `WYE_EXECUTION_PERSISTENCE_FREEZE.md` lo schema
documentale di `0021_scientific_evaluation_publication`: semantic execution
identity, attempt separati, selection/result/trace roots, publication atomica,
governance e downgrade fail-safe. Query projections e report di riconciliazione
estesi restano 0022; result payload scientifici restano review-gated.

```text
Phase 7.6.4B-1:
DESIGN FROZEN — READY FOR PHASE 7.6.4B 0021 IMPLEMENTATION

Phase 7.6.4B-1B:
REPLAY SEMANTICS AMENDMENT FROZEN
```

Il modello REPLAY corretto è stato implementato e committato con la Phase
7.6.4B nel commit `af2b381a4b50223573c9d600bfcae81c6f8402ac`.
REPLAY confronta la pubblicazione storica, persiste una verification immutabile
`matched`/`mismatch` e non crea una nuova pubblicazione scientifica. Il
repository head è 0021; il DB locale resta 0017.

Phase 7.6.4C aggiunge il runtime di persistenza/orchestrazione: crea o riusa
l'identità semantica, lega idempotency key, gestisce attempt/heartbeat/failure,
pubblica atomicamente output canonici già calcolati dal caller e persiste la
verifica REPLAY. Stato: `COMPLETED + COMMITTED`.

La foundation di persistenza/orchestrazione prevista dalla Phase 7.6 è quindi
completa: `PHASE 7.6 COMPLETED`. Il runtime Phase 7.7 non è iniziato.

Restano non implementati l'algoritmo di evidence selection, synthesis, scoring,
worker/recovery, replay scientifico e product target. Nessuna formula, peso,
threshold o score numerico è stato introdotto.

La Phase 7.7.1A congela in `WYE_SELECTION_POLICY_FREEZE.md` il contratto
tecnico machine-executable per la selezione: policy embedded nel protocollo,
validation fail-closed, matrici sugli stati realmente presenti, confini
temporali e di provenance, exact mapping per vocabulary/endpoint/context,
reingestion/dependency boundary, registry reason/rule, precedence e payload
canonici di decision, manifest e trace.

Il confine selection-only è un pure engine/validation harness: nessuna execution
o publication 0021 viene creata e non sono ammessi result/trace fittizi. Il
freeze 7.7.1A non includeva un'istanza scientificamente approvata; 7.7.1B
prepara la policy candidata e i golden expected decisions descritti sotto, ma
non sostituisce la review indipendente.

```text
Phase 7.7.1A:
TECHNICAL CONTRACT FROZEN

Next:
Phase 7.7.1B — Initial Selection Protocol Scientific Review & Golden Cases
```

Il freeze è solo documentale: nessun runtime, test, migration, scoring o replay
scientifico è stato implementato.

La Phase 7.7.1B aggiunge la policy candidata canonica
`efsa_qps_evidence_selection/1.0.0-candidate.1` e 28 golden case scritti come
oracle indipendenti dall'implementazione. Il perimetro è volutamente limitato a
substance/finding/EFSA QPS; OpenFoodTox 3 resta fail-closed finché endpoint e
contesto non hanno mapping scientifici governati.

Il digest candidato è
`d5c98f988ae1ef8514518a97cbc00d1f5c6d5984ae7fea7a60c7c113dc833615`.
Non esiste nel repository un'approvazione nominale di scientific reviewer,
validation owner e release approver. Nessun caso scientifico è quindi
auto-approvato e nessun protocollo viene pubblicato.

```text
Phase 7.7.1B:
CANDIDATE POLICY FROZEN

Next mandatory gate:
independent scientific review + validation-owner approval of the exact policy
digest and mandatory golden oracles
```

Non sono stati creati selector runtime, test eseguibili, migration, synthesis o
scoring. Legacy scoring e database locale restano invariati.

La Phase 7.7.1C prepara il pacchetto di review esterna in
`WYE_SELECTION_POLICY_SCIENTIFIC_REVIEW_PACKAGE.md`. La review è vincolata al
digest candidato
`d5c98f988ae1ef8514518a97cbc00d1f5c6d5984ae7fea7a60c7c113dc833615`
e al corpus di 28 golden case identificato da
`WYE_SELECTION_GOLDEN_CORPUS_MANIFEST.json`. La completezza tecnica del
pacchetto non costituisce approvazione scientifica o autorizzazione alla
pubblicazione.

```text
Phase 7.7.1C:
SCIENTIFIC REVIEW PACKAGE COMPLETED

Phase 7.7.1:
BLOCKED ON EXTERNAL SCIENTIFIC APPROVAL

Next mandatory gate:
external scientific review + validation-owner sign-off + release approval
```

La Phase 7.7.2 aggiunge il gate meccanico fail-closed per ricevere un record
scientifico esterno legato ai digest esatti. Il modulo non crea record, non
attribuisce autorità all'AI e non usa il database. Il percorso riservato
`WYE_SELECTION_POLICY_EXTERNAL_APPROVAL.json` non esiste nel repository;
pertanto il numero di approvazioni scientifiche reali resta `0`.

```text
Phase 7.7.2:
APPROVAL GATE IMPLEMENTED — EXTERNAL SCIENTIFIC APPROVAL REQUIRED

Next:
obtain a governed external scientific-review record for the frozen package
```

La Phase 7.7.3 aggiunge
`WYE_SELECTION_POLICY_EXTERNAL_REVIEW_HANDOFF.md`, un unico punto di ingresso
human-facing per il revisore esterno. Il documento identifica candidate e
corpus tramite i digest congelati, espone scope e fuori-scope, presenta le
undici Category C senza modificarne identità o ordine, spiega la review dei 28
golden case e include una dichiarazione compilabile. Rinvia al review package
e agli artifact canonici per il dettaglio, senza copiarne una nuova fonte
semantica.

La review umana non è ancora avvenuta. Il form non è
`WYE_SELECTION_POLICY_EXTERNAL_APPROVAL.json`, non sblocca il gate e non
pubblica o promuove il candidate.

```text
Phase 7.7.3:
HANDOFF READY — HUMAN REVIEW REQUIRED

Current gate:
EXTERNAL SCIENTIFIC APPROVAL REQUIRED
```
