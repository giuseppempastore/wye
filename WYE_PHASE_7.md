# WYE — Fase 7: Scientific Scoring

## Stato

```text
Fase 7.0   — Architecture & Requirements Review                 COMPLETATA
Fase 7.0.1 — Architecture Specification & Phase 7.0 Freeze     COMPLETATA
Fase 7.1   — Logical protocol / snapshot / execution model      COMPLETATA
Fase 7.2   — Evidence eligibility & selection semantics         COMPLETATA
Fase 7.3   — Endpoint synthesis / substance assessment          COMPLETATA
Fase 7.4   — Substance → ingredient projection                  COMPLETATA
Fase 7.5   — Exposure readiness / product assessment            COMPLETATA
Fase 7.6   — Persistence / explainability / historical replay   COMPLETATA
Fase 7.6.1 — Canonicalization / schema / publication freeze     PROPOSTA, NON INIZIATA
```

La Fase 7.0.1 congela il contratto architetturale iniziale. Non dichiara il
metodo scientificamente validato e non autorizza l'implementazione di formule,
threshold, source weights, migration, API o runtime scoring.

Baseline della review 7.6:

```text
branch: ingredients_score
HEAD: c042401fe57247b6fdb27c57b321a3e3bd4db5a8
origin/ingredients_score: c042401fe57247b6fdb27c57b321a3e3bd4db5a8
Alembic repository head: 0018_scientific_batch_recovery
local database wye: 0017_ingredient_mapping_history
```

Il database locale non è stato aggiornato. Backup, upgrade a `0018` e data
validation restano un task operativo separato.

## Documenti normativi

- `WYE_SCORING_SEMANTICS.md`: semantica, intended use, stati, aggregazione e
  data gap.
- `WYE_SCORING_PROTOCOL.md`: selezione deterministica, conflitti, snapshot,
  riproducibilità, explainability e test vector concettuali.
- `WYE_SCORING_EXECUTION_MODEL.md`: modello logico 7.1 di protocollo/versione,
  snapshot, target freeze, execution, result, trace e determinismo.
- `WYE_EVIDENCE_SELECTION.md`: contratto 7.2 di candidate evidence,
  eligibility, applicability, dependency, decisioni e selection digest.
- `WYE_EVIDENCE_SYNTHESIS.md`: contratto 7.3 di evidence line, comparison
  group, endpoint synthesis e substance hazard profile multidimensionale.
- `WYE_INGREDIENT_PROJECTION.md`: contratto 7.4 di mapping snapshot,
  relationship-aware projection, uncertainty e multi-substance collection.
- `WYE_PRODUCT_ASSESSMENT.md`: contratto 7.5 di product composition snapshot,
  exposure readiness, scenario e risk computability.
- `WYE_SCORING_PERSISTENCE.md`: contratto 7.6 di artifact canonici,
  publication atomica, query projection, explainability e historical replay.
- questo documento: scope, confine legacy, governance, decisioni e roadmap.

In caso di conflitto, i principi non negoziabili e le decisioni esplicite di
questo documento prevalgono sulla documentazione legacy di scope. Un futuro
protocollo pubblicato potrà specializzare questi contratti, ma non violarli.

## Principi congelati

```text
scientific evidence != scientific scoring
AI != scientific source of truth
absence of evidence != evidence of danger

hazard != exposure != risk
confidence != safety
evidence quality != source prestige
missing evidence != negative evidence

same canonical inputs
+ same evidence snapshot
+ same mapping state
+ same scoring protocol version
= same result
```

## Confine legacy

I seguenti componenti sono classificati formalmente:

```text
legacy / excluded from Phase 7 scientific scoring
```

### Runtime e dati statici

- `backend/app/services/scoring.py`;
- `backend/app/data/ingredients.py`: `SOURCE_AUTHORITY_WEIGHTS`,
  `CRITICAL_HARMFUL_CATALOG`, `SCORE_COLOR_RULES`, `CATALOG`;
- endpoint legacy `/analyze` in `backend/app/main.py`;
- inserimento degli score placeholder in `backend/app/main.py`.

### Tabelle e campi legacy

- `ingredients.risk_level` ed `ingredients.evidence_level`;
- `sources.authority_level` e `sources.is_authoritative` quando usati come
  scorciatoia per pesare evidenza;
- `ingredient_risk_profiles`;
- `ingredient_evidence`;
- `product_scores`;
- `cosmetics_products.ingredient_score` e `final_score`;
- `cosmetic_ingredient_assessment`.

### Specifiche storiche non normative

Le formule, le bande, le penalità e le regole di dominanza presenti in
`scope/project_documentation.md`, negli seed SQL e nella documentazione MVP non
sono una specifica scientifica della Fase 7.

Questi componenti non vengono modificati in 7.0.1, non sono input eleggibili per
un futuro protocollo e non devono essere migrati o reinterpretati senza una RFC
dedicata. La futura Fase 7.8 dovrà gestirli in shadow mode e pianificarne la
dismissione controllata.

## Decisioni architetturali

### Primo dominio

Il primo protocollo realisticamente implementabile è:

```text
endpoint-specific evidence synthesis
+ multidimensional substance hazard profile
```

Motivazione:

- Fase 6 conserva assessment e finding con provenance riproducibile;
- EFSA QPS e OpenFoodTox forniscono evidenza eterogenea utile a domande ed
  endpoint specifici;
- la presenza e l'ordine degli ingredienti sono disponibili, ma concentrazione,
  dose, frequenza, durata e scenario di esposizione non lo sono;
- alcuni relationship type ingrediente–sostanza non dimostrano presenza o dose;
- il rischio richiede hazard characterisation ed exposure coerenti con la stessa
  domanda scientifica.

Il primo protocollo non produrrà un quantitative product risk, una dichiarazione
di sicurezza o un generic health score.

### Decisione sullo score numerico

Decisione per il primo protocollo:

```text
C. no numerical score justified for the first protocol
```

Decisione di lungo periodo:

```text
B. numerical score possible later after validation
```

L'opzione B non è una promessa di prodotto. Richiede intended use definito,
dominio separato, input sufficienti, protocollo scientifico approvato,
calibrazione, validazione, analisi di sensibilità e comunicazione verificata. La
Fase 7.0 non definisce scala, direzione, formula, peso, threshold o banda.

### Separazione dei domini

Devono restare protocolli indipendenti:

- toxicological evidence synthesis e hazard profiling;
- exposure assessment e risk characterisation;
- allergen assessment e personalizzazione per allergie;
- nutrition assessment;
- cosmetici;
- integratori;
- consumer preference.

Un composite score fra domini richiederà un protocollo separato e validato. Non
potrà emergere implicitamente dall'aggregazione tecnica dei risultati.

## Governance delle regole

### Ruoli

- **Protocol proposer**: presenta la RFC e gli use case, senza autorità di
  pubblicazione autonoma.
- **Scientific reviewer**: valuta domanda, evidenze, assunzioni, relevance,
  incertezza e claim. Deve includere competenze appropriate al dominio.
- **Data/model steward**: verifica provenance, identità, snapshot, mapping,
  determinismo e compatibilità del modello dati.
- **Validation owner**: mantiene test vector, benchmark, sensitivity analysis e
  impact report indipendenti dall'implementatore.
- **Release approver**: autorizza pubblicazione, deprecazione, ritiro o rollback
  dopo le review richieste.

Una persona può ricoprire più ruoli solo se la RFC documenta il conflitto di
interessi e prevede una review indipendente proporzionata al rischio del claim.

### Lifecycle

```text
draft
→ scientific_review
→ approved
→ published
→ deprecated
→ retired
```

Transizioni eccezionali:

- `scientific_review → draft` per richieste di modifica;
- `approved → draft` se la validazione fallisce prima della pubblicazione;
- `published → deprecated` quando esiste una versione sostitutiva o una
  limitazione nota non urgente;
- `published/deprecated → retired` per ritiro scientifico, errore materiale o
  cessazione d'uso.

`published` è immutabile. Correzioni e rollback producono una nuova versione o
un evento di ritiro auditabile; non modificano in place regole o risultati.

### Contenuto obbligatorio di una RFC

- domanda scientifica, intended use, dominio e claim;
- rationale e riferimenti scientifici verificabili;
- popolazione, endpoint, route, durata e scenario;
- input richiesti e data gap;
- evidence eligibility, conflict e missing-evidence policy;
- quality, relevance, consistency, uncertainty e confidence framework;
- aggregation e explainability contract;
- compatibility e impatto sui risultati storici;
- test vector, benchmark, sensitivity/impact report;
- strategia di rollout, monitoraggio, supersession e ritiro;
- change log e approvazioni nominali/di ruolo.

### Version numbering

Il versionamento deve essere semantico rispetto al contratto osservabile:

- **major**: cambia significato, intended use, claim, dominio o semantica di
  aggregazione;
- **minor**: estende in modo compatibile evidenze, endpoint o regole e può
  modificare risultati;
- **patch**: correzione che non dovrebbe cambiare il risultato semantico.

Qualunque modifica che cambia un risultato pubblicato richiede comunque una
nuova protocol version e un impact report, anche se inizialmente classificata
come patch.

### Pubblicazione, supersession e ritiro

La pubblicazione richiede:

- review scientifica conclusa;
- validation owner sign-off;
- test vector e replay deterministici;
- claim e messaggi di insufficienza approvati;
- canonical digest delle regole;
- change log e versione precedente/sostitutiva esplicite.

Un rollback operativo seleziona una versione già pubblicata e valida per nuove
execution, senza cancellare risultati storici. Una retraction blocca nuove
execution della versione ritirata, conserva audit e spiega il motivo.

## Roadmap finale 7.x

La roadmap precedente è confermata. La specifica non ha prodotto motivi per
cambiarne l'ordine; ha rafforzato il gate fra hazard profiling ed exposure.

| Fase | Obiettivo | Gate principale |
|---|---|---|
| 7.0 | Architecture & Requirements Review | Review repository e confini completati |
| 7.0.1 | Specification & Phase 7.0 Freeze | Contratti documentali e decisioni esplicite |
| 7.1 | Logical protocol / snapshot / execution model | ADR e schema logico approvati; nessuna formula |
| 7.2 | Evidence eligibility & selection semantics | Contratto deterministico e auditabile; nessun runtime |
| 7.3 | Endpoint-specific synthesis / substance assessment | Contratto multidimensionale definito; regole scientifiche da review esterna |
| 7.4 | Substance → ingredient projection | Contratto relationship-aware definito; composition/form review-gated |
| 7.5 | Exposure readiness / ingredient → product assessment | Exposure sufficiente o `risk_not_computable` |
| 7.6 | Persistence / explainability / historical replay | Contratto completato; migration subordinata al freeze 7.6.1 |
| 7.6.1 | Canonicalization / schema / publication freeze | Proposta tecnica, non iniziata |
| 7.7 | Validation / expert review / sensitivity analysis | Validazione esterna prima di claim o numeri |
| 7.8 | API shadow mode / legacy comparison | Nessuna sostituzione silenziosa del legacy |
| 7.9 | Governed rollout / legacy retirement | Rollout, monitoraggio e ritiro auditabile |

La Fase 7.6 è completata come specifica architetturale documentale. Non ha
creato migration né runtime. La decisione di migration è B: prima di autorizzare
lo schema devono essere congelati canonicalization profile, artifact envelope,
vincoli SQL, publication/reconciliation, engine retention, privacy e query
projections. La Fase 7.6.1 non è iniziata da questo checkpoint.

## Phase 7.0 exit review

Le classificazioni descrivono lo stato al freeze architetturale. `APPROVED`
significa approvato come vincolo architetturale, non scientificamente validato.

| Deliverable | Stato | Nota |
|---|---|---|
| Scoring Semantic Charter | DEFINED BUT REQUIRES EXTERNAL SCIENTIFIC REVIEW | Definizioni e limiti congelati; terminologia da review di dominio |
| Intended Use & Claims Matrix | DEFINED BUT REQUIRES EXTERNAL SCIENTIFIC REVIEW | Claim conservativi; revisione scientifica e legale prima dell'uso esterno |
| Evidence Eligibility Policy | DEFINED BUT REQUIRES EXTERNAL SCIENTIFIC REVIEW | Contratto deterministico definito; criteri concreti appartengono al protocollo |
| Conflict Policy | DEFINED BUT REQUIRES EXTERNAL SCIENTIFIC REVIEW | Nessuna media o precedence globale |
| Quality / Confidence / Uncertainty Framework | DEFINED BUT REQUIRES EXTERNAL SCIENTIFIC REVIEW | Dimensioni separate; nessuna scala numerica |
| Aggregation Specification | DEFINED BUT REQUIRES EXTERNAL SCIENTIFIC REVIEW | Semantica strutturale definita; regole endpoint-specific da validare |
| Missing Evidence Policy | APPROVED | Stati e non-penalizzazione sono vincoli architetturali |
| Versioning & Reproducibility Contract | APPROVED | Entità logiche, immutabilità e modalità storiche definite |
| Explainability Contract | APPROVED | Trace scientifico obbligatorio e AI non autoritativa |
| Governance / RFC process | APPROVED | Lifecycle, ruoli e change control definiti |
| Data Gap Matrix | APPROVED | Fotografia dello schema corrente; da rivalutare per ogni protocollo |
| Conceptual Test Vectors | DEFINED BUT REQUIRES EXTERNAL SCIENTIFIC REVIEW | Expected status senza formule definiti |
| First-domain decision | APPROVED | Evidence synthesis / hazard profile |
| Numeric-score decision | APPROVED | C per il primo protocollo; B solo come possibilità futura validata |

Conclusione del gate:

```text
architecture defined and frozen
scientific validation not yet completed
runtime implementation not authorised by Phase 7.0.1
```
