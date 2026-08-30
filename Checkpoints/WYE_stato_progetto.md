# WYE — Stato del progetto

## Baseline corrente

```text
branch: ingredients_score
HEAD: 0ea3a26283f617e5cc07e7ad83c04c7fa20a67af
origin/ingredients_score: 48a0681e7e928bec47441d468c86f20784d00ea5
Alembic repository head: 0020_scientific_evidence_snapshots
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
Fase 7.6.3A IMPLEMENTED + VALIDATED — PENDING COMMIT
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

Al termine della 7.6.2B serializer e artifact writer non erano implementati;
snapshot repository/finalizer, execution e replay runtime restano tuttora non
implementati. Non sono stati introdotti motori scientifici, formule, pesi,
threshold o score numerici; lo scoring legacy resta isolato.

## Fase 7.6.3A

`wye-c14n-json-v1` e il scientific artifact writer inline sono implementati e
validati, pending commit. Il serializer applica NFC, UTF-8, ordinamento key per
byte, escaping canonico, signed 64-bit integer e rifiuto dei binary float e dei
tipi Python non normalizzati. L'allowlist runtime copre `protocol_definition/1`,
`protocol_review/1` e i tre artifact snapshot v1.

Il writer calcola internamente SHA-256, inserisce o riusa l'identità canonica,
verifica metadata/cache/byte autoritativi, crea o riusa una location inline
verified e lascia commit/rollback al chiamante. Retry e concorrenza convergono
sulla stessa artifact/location identity; mismatch o bytes non dimostrabili
producono errori espliciti.

## Prossimo gate

Il successivo checkpoint non è iniziato e richiederà autorizzazione separata.
Snapshot repository, builder/finalizer, mapping-state runtime persistence, scoring execution,
execution/result persistence, replay/reproduce/recalculate e motore scientifico
deterministico restano non implementati. L'upgrade del database locale resta un
task operativo separato.
