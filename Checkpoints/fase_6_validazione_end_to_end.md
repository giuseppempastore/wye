# WYE — Fase 6: validazione end-to-end conclusiva

## Stato

```text
FASE 6.4.5 COMPLETATA
FASE 6.4 COMPLETATA
FASE 6 COMPLETATA
```

Baseline di validazione: `ingredients_score`, dopo il merge della Fase 6.4.4.

Alembic repository head:

```text
0018_scientific_batch_recovery
```

## Gate validati

- EFSA QPS e OpenFoodTox 3.0: acquisizione reale bounded, artifact-first e
  persistence PostgreSQL validate.
- Source, dataset, release, artifact, ingestion run, assessment e finding:
  provenance completa e immutabile.
- Identificatori verificati: risoluzione verso sostanze attive; identificatori
  sconosciuti: candidate/review, senza creazione automatica.
- Ingredient-substance bridge: proposal, decision, materialization e history
  controllate.
- Batch multi-provider: checkpoint persistente, retry bounded, resume dopo crash,
  stale-lease reclaim, concorrenza e changed-upstream conflict.
- Reprocessing: parser/configuration version differenti producono run storiche
  distinte senza overwrite.
- Failure injection: acquisition, artifact, parser, identity, assessment e finding;
  nessun assessment parziale o finding orfano.
- Traversal completo:

```text
product
→ extraction item
→ canonical ingredient
→ accepted ingredient_substance
→ active substance
→ verified substance_identifier
→ scientific assessment
→ scientific finding
→ ingestion run
→ artifact
→ release
→ dataset
→ source
```

Il traversal è stato validato anche con evidenza prodotta dal batch/recovery path.

## Regressione e rete

La regressione scientifica offline è eseguita con `PYTHON_DOTENV_DISABLED=1` e
opt-in reali disabilitati. In tale modalità:

```text
0 EFSA remote calls
0 OpenFoodTox remote calls
0 OpenAI calls
0 Gemini calls
0 remote S3 calls
0 uncontrolled external HTTP calls
```

I test reali dei due provider restano separati ed esplicitamente opt-in.

## Confine con la Fase 7

```text
scientific evidence != scientific scoring
AI != scientific source of truth
```

La Fase 6 non introduce ranking, weighting, aggregazione o scoring. La Fase 7
dovrà progettare selezione dell'evidenza, conflitti, confidence, aggregazione,
versioning, explainability e insufficient-evidence behavior.

## Database locale

Il database persistente `wye` è intenzionalmente ancora a
`0017_ingredient_mapping_history`. L'allineamento richiede un task operativo
separato:

```text
backup
→ upgrade 0017 → 0018
→ data validation
```

Nessun upgrade del database persistente è stato eseguito durante la closure.
