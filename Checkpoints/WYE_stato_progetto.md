# WYE — Stato del progetto

## Baseline corrente

```text
branch: ingredients_score
HEAD: c042401fe57247b6fdb27c57b321a3e3bd4db5a8
origin/ingredients_score: c042401fe57247b6fdb27c57b321a3e3bd4db5a8
Alembic repository head: 0018_scientific_batch_recovery
local database wye: 0017_ingredient_mapping_history
```

Il database locale deve essere aggiornato separatamente tramite backup, upgrade a
`0018` e validazione. La Fase 7.6 non modifica il database.

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
Fase 7.6.1  PROPOSTA, NON INIZIATA — Canonicalization/schema/publication freeze
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

- `WYE_PHASE_7.md`;
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

## Prossimo gate

Il checkpoint proposto è `Phase 7.6.1 — Canonicalization, Persistence Schema and
Publication Protocol Freeze`. Non è iniziato. La Fase 7.7 non deve usare runtime
persistito finché questi gap tecnici non sono risolti.

L'upgrade del database locale resta un task operativo separato.
