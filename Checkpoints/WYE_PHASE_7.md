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
Fase 7.6.1 — Canonicalization / schema / publication freeze     COMPLETATA
Fase 7.6.2A — Scientific evaluation persistence foundation      IMPLEMENTATA E VALIDATA
Fase 7.6.2B-1 — Scientific evidence snapshots design/freeze      COMPLETATA
Fase 7.6.2B-2 — Scientific evidence snapshots migration          IMPLEMENTED + VALIDATED
Fase 7.6.3A — Canonical serialization / artifact writer           COMPLETED + COMMITTED
Fase 7.6.3B — Evidence snapshot repository / builder / finalizer  COMPLETED + COMMITTED
Fase 7.6.4A-1 — Mapping state / canonical input design freeze     DESIGN FROZEN — READY FOR IMPLEMENTATION
Fase 7.6.4A-1B — Mapping authority multiplicity amendment         AUTHORITY MULTIPLICITY AMENDMENT FROZEN
Fase 7.6.4A-2 — Mapping state / canonical input runtime           COMPLETED + COMMITTED
Fase 7.6.4B-1 — Execution / result persistence design freeze      DESIGN FROZEN — READY FOR 0021 IMPLEMENTATION
Fase 7.6.4B-1B — REPLAY publication semantics amendment            REPLAY SEMANTICS AMENDMENT FROZEN
Fase 7.6.4B-2 — Execution / result persistence migration          COMPLETED + COMMITTED
Fase 7.6.4C — Scientific evaluation execution runtime              COMPLETED + COMMITTED
```

La Fase 7.0.1 congela il contratto architetturale iniziale. Non dichiara il
metodo scientificamente validato e non autorizza l'implementazione di formule,
threshold, source weights, migration, API o runtime scoring.

Baseline del freeze 7.6.4A-1:

```text
branch: ingredients_score
HEAD: f775e0e03a4cce348afc07c052d5a72a7c8568c1
origin/ingredients_score: 48a0681e7e928bec47441d468c86f20784d00ea5
Alembic repository head: 0020_scientific_evidence_snapshots
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
- `WYE_MAPPING_EXECUTION_INPUT_FREEZE.md`: freeze 7.6.4A-1 di target identity,
  mapping state e canonical non-protocol execution input.
- `WYE_EXECUTION_PERSISTENCE_FREEZE.md`: freeze 7.6.4B-1 di execution identity,
  attempt, selection/result/trace roots, publication atomica e schema 0021.
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
- `WYE_SCORING_SCHEMA_FREEZE.md`: freeze tecnico 7.6.1 di canonicalizzazione,
  schema logico, vincoli, publication protocol e migration decomposition.
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
| 7.6.1 | Canonicalization / schema / publication freeze | Completata; decisione READY FOR MIGRATION IMPLEMENTATION |
| 7.6.2A | Scientific evaluation persistence foundation | `0019` implementata e validata |
| 7.6.2B-1 | Scientific evidence snapshots design/freeze | Completata; READY FOR MIGRATION IMPLEMENTATION |
| 7.6.2B-2 | Scientific evidence snapshots migration | IMPLEMENTED + VALIDATED |
| 7.6.3A | Canonical serialization / scientific artifact writer | COMPLETED + COMMITTED |
| 7.6.3B | Evidence snapshot repository / builder / finalizer | COMPLETED + COMMITTED (`f775e0e03a4cce348afc07c052d5a72a7c8568c1`) |
| 7.6.4A-1 | Mapping state / canonical execution input design freeze | DESIGN FROZEN — READY FOR IMPLEMENTATION |
| 7.6.4A-1B | Mapping authority multiplicity / unresolved observations | AUTHORITY MULTIPLICITY AMENDMENT FROZEN |
| 7.6.4A-2 | Mapping state / canonical execution input runtime | COMPLETED + COMMITTED |
| 7.6.4B-1 | Scientific execution / result persistence freeze | DESIGN FROZEN — READY FOR 0021 IMPLEMENTATION |
| 7.6.4B-2 | Scientific execution / result persistence migration | COMPLETED + COMMITTED (`af2b381a4b50223573c9d600bfcae81c6f8402ac`) |
| 7.6.4C | Scientific evaluation execution runtime foundation | COMPLETED + COMMITTED |
| 7.7 | Validation / expert review / sensitivity analysis | Validazione esterna prima di claim o numeri |
| 7.8 | API shadow mode / legacy comparison | Nessuna sostituzione silenziosa del legacy |
| 7.9 | Governed rollout / legacy retirement | Rollout, monitoraggio e ritiro auditabile |

La Fase 7.6.1 risolve il gate B della 7.6 congelando canonicalization profile,
digest, artifact envelope, schema logico, vincoli, publication/recovery,
retention, privacy, workload e quattro migration slice. La decisione corrente è
`READY FOR MIGRATION IMPLEMENTATION`, limitata al checkpoint 7.6.2A e alla
migration `0019_scientific_evaluation_foundation`, ora implementata e validata.
Nessun runtime scientifico è stato creato.

La Fase 7.6.2A implementa la sola foundation autorizzata: artifact registry e
location, protocol family/version, governance append-only, vincoli/indici,
immutabilità e lifecycle governato. La revision descrittiva richiede
`alembic_version.version_num VARCHAR(64)` al posto del default storico a 32
caratteri. Snapshot, execution, result, trace, publication e projection restano
fuori scope e saranno trattati soltanto dalle slice successive. Il database
locale resta a `0017_ingredient_mapping_history`.

La Fase 7.6.2B-1 congela lo snapshot come candidate universe tecnico,
protocol-independent e content-addressed. Finding è il membro atomico normale,
assessment è contesto obbligatorio e mapping/target/selection restano input o
output separati. Lifecycle `building -> sealed`, manifest canonico, provenance,
immutabilità, concurrency/idempotency, preflight, downgrade e piano test sono
definiti in `WYE_SCORING_SCHEMA_FREEZE.md`.

Decisione:

```text
DESIGN FROZEN — READY FOR MIGRATION IMPLEMENTATION
```

La migration `0020_scientific_evidence_snapshots` implementa snapshot e membri,
sealing immutabile, artifact binding, governance concreta, preflight e downgrade
fail-safe. Il repository Alembic head è `0020_scientific_evidence_snapshots`.
La migration 7.6.2B, da sola, non implementava serializer, artifact writer,
snapshot repository o finalizer runtime, execution, replay o motori scientifici.

La Fase 7.6.3A implementa il runtime ristretto autorizzato: serializer
`wye-c14n-json-v1`, allowlist kind/schema e writer PostgreSQL caller-transaction
con location inline verified. Identità, SHA-256 e byte comparison sono sempre
ricalcolati dal writer; retry e concorrenza convergono senza mutare artifact
esistenti. I binary float restano vietati: decimal/date/time/UUID/bytes devono
essere trasformati da futuri adapter schema-aware in valori JSON canonici.

La Fase 7.6.3B implementa repository e service caller-transaction-owned per
costruire il candidate universe esplicito, materializzare artifact query/member/
manifest, ordinare i membri deterministicamente e sigillare atomicamente
`building -> sealed`. `status_as_of` materializza
`scientific_assessments.assessment_status`; lo stato della release resta distinto
nel payload provenance e lo schema corrente non inventa lifecycle per finding.
Retry e builder concorrenti convergono soltanto dopo verifica dei root canonici;
le race seal/member mutation sono serializzate dai lock della 0020.

Mapping-state runtime, eligibility/selection, execution/result persistence,
scoring execution, replay e motori scientifici non sono implementati.

La Fase 7.6.4A-1 congela in
`WYE_MAPPING_EXECUTION_INPUT_FREEZE.md` il primo target vocabulary
(`substance`, `ingredient`), il mapping state autorevole/materializzato con
`mapping_day = DATE(as_of UTC)`, gli artifact target/member/manifest/input e il
digest graph non ambiguo. `input_digest` copre target e mapping state, ma non
snapshot evidence, protocollo, mode o configuration; questi root si combinano
solo nel futuro `semantic_execution_digest`. `product` resta escluso finché una
composition/scenario snapshot replay-safe non sarà congelata e implementata.

Il runtime 7.6.4A può usare l'artifact registry 0019 senza una nuova migration.
La futura 0021 dovrà invece referenziare esplicitamente protocol version,
evidence snapshot, target artifact, mapping-state artifact, input artifact e
configuration artifact. Nessun runtime 7.6.4A e nessuna 0021 sono implementati
da questo freeze.

La Fase 7.6.4A-1B corregge il presupposto di cardinalità emerso al primo gate
runtime: un mapping member rappresenta un solo bridge `ingredient_substances`,
mentre `authority_chains[]` conserva tutte le chain proposal/accept/
materialization valide e visibili. `applied` e `already_current` sono provenance
senza precedence; più chain non duplicano il bridge member. Il freeze definisce
inoltre observation identity/payload/reason codes, ordinamenti e la precedence
deterministica fra `resolved`, `empty`, `partially_resolved` e
`history_unavailable`. Non serve una migration. La 7.6.4A-2 implementa ora il
runtime content-addressed di target `substance`/`ingredient`, mapping member con
authority chain multiple, osservazioni, mapping manifest e canonical input. La
Phase 7.6.4A è `COMPLETED + COMMITTED`; la 7.6.4B-1 congela soltanto il
contratto documentale della futura 0021 e non implementa migration o runtime.

## Phase 7.6.4B-1 execution and publication freeze

`WYE_EXECUTION_PERSISTENCE_FREEZE.md` congela una sola identità semantica per
la tupla protocollo, snapshot, input, mode, configurazione e comparison root,
con tentativi operativi separati e append-only dopo la chiusura. La
configurazione v1 contiene il contratto engine semantico e nessun parametro;
il build concreto appartiene al tentativo.

La `0021_scientific_evaluation_publication` crea execution, attempts, selection
decisions, generic result/components, trace, atomic publication, replay
verification e idempotency operativa, estendendo governance con FK concrete a
execution e result. Query projection e replay reports estesi restano nella
slice 0022. Il bundle canonico lega semantic execution, selection, result e
trace; nessun projection digest è canonico.

```text
Phase 7.6.4B-1:
DESIGN FROZEN — READY FOR PHASE 7.6.4B 0021 IMPLEMENTATION

Phase 7.6.4B-1B:
REPLAY SEMANTICS AMENDMENT FROZEN
```

Phase 7.6.4B-2 implements and validates the bounded migration without adding an
execution engine. The repository head is now
`0021_scientific_evaluation_publication`; the local `wye` database remains at
`0017_ingredient_mapping_history`. Status before Git finalization:

```text
COMPLETED + COMMITTED
```

L'amendment 7.6.4B-1B mantiene l'identità globale content-addressed 0019 e
definisce REPLAY come verifica di una pubblicazione storica. Un REPLAY concluso
ha una verification immutabile `matched`/`mismatch`, non una nuova publication
scientifica né nuovi result/trace/selection rows. NORMAL, REFRESH e
COUNTERFACTUAL continuano invece a richiedere la pubblicazione canonica.

La migration corretta è stata completata e committata come Phase 7.6.4B nel
commit `af2b381a4b50223573c9d600bfcae81c6f8402ac`.

## Phase 7.6.4C execution runtime foundation

Phase 7.6.4C implementa l'orchestrazione provider-neutral sopra 0021: identità
semantica e idempotenza, attempt e lease, persistenza atomica di output canonici
forniti esplicitamente dal caller e REPLAY verification-only `matched` /
`mismatch`. Tutti gli artifact usano `ScientificArtifactWriter`; repository e
service non eseguono commit o rollback nascosti. NORMAL, REFRESH e
COUNTERFACTUAL producono publication; REPLAY riusa gli artifact globali e non
crea result/trace/selection/publication propri.

```text
Phase 7.6.4C:
COMPLETED + COMMITTED
```

Il runtime non contiene algoritmo di evidence selection, synthesis, scoring,
worker/recovery o product target. Non introduce formule, pesi, threshold o
score numerici.

Con questa foundation, tutti i deliverable di persistenza e orchestrazione
previsti dalla Phase 7.6 sono disponibili. `PHASE 7.6 COMPLETED`; gli algoritmi
scientifici restano nel perimetro successivo e il runtime Phase 7.7 non è
iniziato.

## Phase 7.7.1A deterministic selection-policy freeze

Il primo slice scientifico corretto resta la selezione deterministica dei
candidati di uno snapshot sealed. `WYE_SELECTION_POLICY_FREEZE.md` congela il
contratto tipizzato `wye_scientific_evidence_selection_policy/1`, embedded in
`protocol_definition/1`: executability fail-closed, candidate/status/time/run e
representation gates, mapping esatti per vocabulary/endpoint/context, reason e
rule registry chiusi, precedence, decision/manifest/trace canonici.

Il selector 7.7.1 è congelato come pure engine/validation harness: non crea
execution o publication 0021 e non inventa result/trace. I valori scientifici
concreti — allowlist, mapping, disposition per unknown/dependency e golden
expected decisions — non sono stati inventati dal freeze tecnico. Il checkpoint
7.7.1B prepara una policy candidata; l'approvazione resta un gate scientifico
esterno e indipendente.

```text
Phase 7.7.1A:
TECHNICAL CONTRACT FROZEN

Next:
Phase 7.7.1B — Initial Selection Protocol Scientific Review & Golden Cases
```

Nessun runtime Phase 7.7, policy scientifica, formula, peso, threshold o score
numerico è stato introdotto da questo freeze.

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

## Phase 7.7.1B initial selection policy candidate

Il checkpoint 7.7.1B materializza una prima istanza candidata, senza
auto-approvazione scientifica:

```text
policy: efsa_qps_evidence_selection / 1.0.0-candidate.1
selection_policy_digest:
  d5c98f988ae1ef8514518a97cbc00d1f5c6d5984ae7fea7a60c7c113dc833615
scope: substance + finding + EFSA QPS only
status: CANDIDATE — AWAITING EXTERNAL SCIENTIFIC APPROVAL
```

La policy nega OpenFoodTox 3 in questa istanza perché endpoint, route,
duration e population non sono ancora normalizzati in modo governato; non è
un giudizio di qualità o una precedence fra provider. Il corpus
`WYE_SELECTION_GOLDEN_CASES.md` contiene 28 oracle author-written, distinti fra
meccanica `TECHNICAL` e decisioni `SCIENTIFIC-REVIEW-REQUIRED`. Nessun caso è
marcato `SCIENTIFIC-APPROVED`.

Mancano reviewer scientifico indipendente, validation-owner sign-off e release
approval sul digest esatto. Il selector di produzione resta quindi bloccato;
un eventuale interpreter tecnico successivo potrà usare soltanto policy
sintetiche in harness non produttivo, senza publication 0021.

```text
Phase 7.7.1B:
CANDIDATE POLICY FROZEN
```

## Phase 7.7.1C scientific review package

Il checkpoint 7.7.1C organizza il gate esterno senza auto-approvare la policy.
`WYE_SELECTION_POLICY_SCIENTIFIC_REVIEW_PACKAGE.md` contiene la matrice
esaustiva A/B/C/D, le review card, la source-evidence table, la matrice dei 28
golden case, i ruoli e il record di approvazione vincolato ai digest esatti.
`WYE_SELECTION_GOLDEN_CORPUS_MANIFEST.json` identifica il corpus sottoposto a
review. Policy e corpus restano candidati; nessun protocollo è pubblicabile
finché scientific reviewer, validation owner e release approver non completano
il gate documentato.

```text
Phase 7.7.1C:
SCIENTIFIC REVIEW PACKAGE COMPLETED

Phase 7.7.1:
BLOCKED ON EXTERNAL SCIENTIFIC APPROVAL
```

## Phase 7.7.2 external scientific approval gate

È implementato il validatore repository-native del record esterno
`wye_selection_policy_approval_record/1`. Il gate ricalcola i digest congelati,
richiede identità reviewer, timestamp UTC, conferme esplicite, scope completo,
Category C complete per `approved`, audit reference e digest del record. Non
crea approval artifact, non usa il DB e non pubblica la policy.

`WYE_SELECTION_POLICY_EXTERNAL_APPROVAL.json` è assente: approvazioni esterne
reali `0`. Il candidato resta invariato e bloccato.

```text
Phase 7.7.2:
APPROVAL GATE IMPLEMENTED — EXTERNAL SCIENTIFIC APPROVAL REQUIRED
```
