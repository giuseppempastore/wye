# WYE — Stato del progetto

## Baseline corrente

```text
branch: ingredients_score
HEAD: 398581fe93b154ffdb49d6a93005485f6888bbca
origin/ingredients_score: 398581fe93b154ffdb49d6a93005485f6888bbca
Alembic repository head: 0018_scientific_batch_recovery
local database wye: 0017_ingredient_mapping_history
```

Il database locale deve essere aggiornato separatamente tramite backup, upgrade a
`0018` e validazione. La Fase 7.2 non modifica il database.

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
Fase 7.3    NON INIZIATA
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

## Prossimo gate

La Fase 7.3 potrà iniziare solo con istruzione esplicita. Dovrà definire
endpoint-specific synthesis, evidence-line appraisal, comparability completion,
agreement/discordance, conflict handling, sufficiency, uncertainty e il primo
substance assessment multidimensionale, con review scientifica esterna.

L'upgrade del database locale resta un task operativo separato.
