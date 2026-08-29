# WYE — Stato del progetto

## Baseline corrente

```text
branch: ingredients_score
HEAD: 27b7edbab4caa76abd5d2e67f5aa45e6b1128445
origin/ingredients_score: 27b7edbab4caa76abd5d2e67f5aa45e6b1128445
Alembic repository head: 0018_scientific_batch_recovery
local database wye: 0017
```

Il database locale deve essere aggiornato separatamente tramite backup, upgrade a
`0018` e validazione. La Fase 7.0.1 non modifica il database.

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
Fase 7.1    NON INIZIATA
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

## Prossimo gate

La Fase 7.1 potrà iniziare solo con istruzione esplicita e dopo aver accettato che:

- l'architettura è definita, ma il metodo non è ancora scientificamente validato;
- il primo protocollo non produce uno score numerico;
- i criteri scientifici concreti richiedono review esterna di dominio;
- il logical protocol/snapshot/execution model deve essere progettato prima di
  migration o runtime;
- l'upgrade del database locale resta un task operativo separato.
