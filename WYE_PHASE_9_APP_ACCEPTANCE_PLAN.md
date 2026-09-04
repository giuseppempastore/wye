# WYE — Phase 9 App Acceptance Plan

## 1. Autorità, obiettivo e non-autorizzazioni

Questo è il piano autorevole per l'accettazione sistematica, su dispositivo reale, di ogni funzione prevista o visibile dell'app WYE MVP. La Phase 8 è la baseline di implementazione/integration preparation secondo `WYE_PHASE_8_TO_9_TRANSITION.md`; non è accettazione finale.

Restano vietati scoring runtime, overall numerico, produzione e release. WYE tratta soltanto alimenti confezionati e offre indicazioni generali, approssimative e informative. Non offre consiglio medico/clinico/terapeutico/dietetico personalizzato, dose/porzione/frequenza, né claim di sicurezza, salubrità, compliance, certificazione o idoneità individuale. Zero, missingness, evaluability, copertura, confidenza e incertezza devono mantenere le distinzioni definite in Phase 7/8.

Documenti autorevoli per i test: questo piano; `WYE_PHASE_9_FEATURE_ACCEPTANCE_MATRIX.md`; `WYE_PHASE_9_TEST_FEEDBACK_GUIDE.md`; `WYE_PHASE_8_TO_9_TRANSITION.md`. Il postmortem Phase 8 è evidenza storica autorevole. Runbook, log template e self-test Phase 8 sono riferimenti tecnici parzialmente autorevoli per il solo percorso mobile canonico e subordinati a questi documenti.

## 2. Regole comuni di esecuzione e stato

- Ogni run usa commit noto, `test_session_id`, test-case ID stabile, device/OS e dataset non sensibile controllato.
- Prima di ogni subfase: working tree atteso, ambiente locale/dev, feature flag e servizi strettamente necessari; nessun provider o servizio di produzione.
- Un test alla volta; evidenza minima secondo la guida feedback; nessun log raw.
- Risultati matrice: `NOT_RUN`, `PASS`, `FAIL`, `BLOCKED`, `DEFERRED`, `OUT_OF_SCOPE`, `ACCEPTED`.
- `ACCEPTED` richiede tutti i casi obbligatori `PASS`, nessun blocker critical/high, evidenza sanitizzata, vincoli Phase 7/8 rispettati, nessun fallback legacy/scoring e approvazione product owner con data.
- Un checkpoint review/commit chiude una subfase ma non è una subfase funzionale aggiuntiva. Commit e push richiedono autorizzazione separata.

## 3. Severità difetti e stop condition comuni

| Severità | Regola |
| --- | --- |
| `CRITICAL` | Esposizione di segreti/dati vietati, uso di produzione, claim medico/sicurezza/certificazione, scoring o overall non autorizzato, perdita/corruzione dati, bypass auth. Stop immediato; nessuna accettazione. |
| `HIGH` | Crash/hang, funzione MVP primaria inutilizzabile, fallback legacy, zero/missingness confusi, percorso canonico rotto, permessi senza recupero, evidenza inaffidabile. Blocca subfase e accettazione. |
| `MEDIUM` | Comportamento errato con workaround sicuro, persistenza/lifecycle/accessibilità degradati, messaggio o retry fuorviante. Richiede triage e decisione prima del gate finale. |
| `LOW` | Difetto cosmetico o copy non ambiguo che non altera sicurezza, significato o completamento. Può essere registrato per follow-up con approvazione esplicita. |

Stop comuni: route `/analyze` o `/analyze-image` durante un caso non autorizzato; provider esterno; score/overall fallback; segreto/URL firmato/base64/raw OCR/payload/traceback nei log o screenshot; ambiente/commit non previsto; retry oltre il limite del caso; azione distruttiva o produzione. Lo stop genera feedback `STOPPED`, defect e risultato matrice `FAIL` o `BLOCKED`.

## 4. Subfasi funzionali

### 9.0 — Acceptance scope e feature inventory

- Scope: ispezione read-only, transizione 8→9, inventario completo, matrice, workflow feedback, logging-gap e authority audit.
- Prerequisiti: branch/HEAD/origin 0/0, tree/staging puliti, documenti Phase 7/8/E2E presenti.
- Casi positivi: ogni funzione visibile/integration-facing ha ID, posizione, goal, dipendenza, stato, MVP status, test, evidenza, rischio e owner; tutti i documenti richiesti sono coerenti.
- Casi negativi: rilevare controlli visibili incompleti, legacy/demo/deferred, claim obsoleti, persistenza fittizia, log raw e link mancanti; nessuna approvazione prematura.
- Device/manual: nessun test device; revisione manuale di codice e documenti.
- Automatici: solo Git read-only, `git diff --check`, struttura/link Markdown e scan anti-segreti.
- Evidenza: quattro documenti Phase 9, due rinvii roadmap minimi, diff sanitizzato e stato Git.
- PASS: inventario completo, nessun `ACCEPTED`, controlli meccanici puliti. FAIL: funzione senza ID/campo o affermazione non supportata. Stop: preflight inatteso o contenuto vietato.
- Difetti/approvazione: regole comuni; product owner approva scope, classificazioni e trasferimento 8.7/8.8. Checkpoint: review dei soli documenti, poi commit separatamente autorizzato.

### 9.1 — Workflow autonomo di test, feedback e logging

- Scope: progettare e, previa autorizzazione, implementare un generatore guidato/one-command di pacchetto evidenze sanitizzato e correlabile.
- Prerequisiti: 9.0 approvata; schema feedback congelato; allowlist e corpus negativo concordati.
- Casi positivi: raccolta per session/test ID, eventi frontend e summary backend minimi, export deterministico, clear/cleanup.
- Casi negativi: token, URL firmati, query signature, base64, OCR/provider text, payload/body, path e traceback vengono rifiutati/redatti fail-closed; input malformato non produce pacchetto.
- Device/manual: operatore non sviluppatore genera, revisiona, copia e pulisce un pacchetto su telefono/PC.
- Automatici: unit/golden/negative tests del sanitizer; secret patterns; limite dimensione; correlazione e schema.
- Evidenza: pacchetto campione sicuro, report scanner, test output sintetico, nessun contenuto vietato.
- PASS: unico pacchetto allowlisted riproducibile e guida eseguibile. FAIL: raccolta manuale indispensabile, falso “safe”, correlazione ambigua. Stop: qualunque leakage.
- Difetti/approvazione: `CRITICAL` per leakage/bypass; `HIGH` per pacchetto incompleto o non correlabile. Product owner approva formato e facilità operativa. Checkpoint: review security/privacy + commit dedicato.

### 9.2 — Ambiente, startup e LAN acceptance

- Scope: startup app, config default-off, backend/storage locali autorizzati, raggiungibilità LAN e teardown.
- Prerequisiti: 9.1; device e rete isolata noti; credenziali temporanee; runbook aggiornato; servizi locali autorizzati esplicitamente.
- Casi positivi: app parte senza crash; API e storage locali raggiungibili dal device; token breve e teardown verificati.
- Casi negativi: base URL errata, backend/storage spenti, token assente/scaduto, facade disabilitata, rete diversa.
- Device/manual: cold/warm start, conferma host LAN senza registrare URL completi, messaggi comprensibili.
- Automatici: config parsing e fail-closed già esistenti più eventuali smoke locali autorizzati; nessun provider esterno.
- Evidenza: commit/device/OS, stati UI, status/codici sicuri, shutdown; mai URL/token completi.
- PASS: avvio/raggiungibilità ripetibili e failure sicure. FAIL: localhost/emulator fallback sul telefono, cleartext/config non controllata o startup fragile. Stop: produzione/provider/leakage.
- Difetti/approvazione: common rules, LAN/startup MVP rotto=`HIGH`. Product owner approva readiness del banco prova. Checkpoint: environment review + commit delle sole correzioni autorizzate.

### 9.3 — App shell, Home e navigazione

- Scope: Home, asset, CTA, bottom navigation, back behavior, route note e 404.
- Prerequisiti: 9.2 PASS; nessuna chiamata backend necessaria per shell.
- Casi positivi: Home renderizza, CTA aprono route corretta, tab coerenti, 404 torna Home.
- Casi negativi: route ignota/deep link malformato, tap ripetuto, back stack, asset assente.
- Device/manual: portrait/landscape ove supportato, scroll, label/tooltip, area sicura e recent scans.
- Automatici: router/widget tests e verifica asset/route table.
- Evidenza: test ID, screenshot revisionati delle sole superfici non sensibili, risultato route.
- PASS: nessun dead end; recent scans è dichiarato placeholder/non accettato finché non usa dati reali. FAIL: CTA errata, 404 senza recupero, placeholder presentato come reale.
- Stop/difetti/approvazione: fallback legacy=`HIGH`; difetto navigazione primaria=`HIGH/MEDIUM`. Product owner approva shell/copy. Checkpoint: UX/router review + commit.

### 9.4 — Barcode scanning e inserimento manuale

- Scope: camera scanner, debounce/validità, manual entry e scanner nel form add-product.
- Prerequisiti: 9.3; permesso camera e barcode test controllati; lookup locale disponibile per casi end-to-end.
- Casi positivi: rilevamento singolo, manual submit, clear, loading, routing al dettaglio.
- Casi negativi: permesso negato, codice vuoto/corto/malformato, duplicati rapidi, cancellazione dialog.
- Device/manual: luce/scarsa luce, orientamento, autofocus, tastiera, device senza camera.
- Automatici: validazione/debounce/provider/widget con fake; nessuna camera simulata conta come accettazione reale.
- Evidenza: ID caso, risultato, barcode di fixture non sensibile, nessuna immagine.
- PASS: una sola lookup valida, errori recuperabili. FAIL: loop richieste, crash permesso, accettazione input invalido non motivata.
- Stop/difetti/approvazione: privacy/permesso o funzione primaria rotta=`HIGH`. Product owner approva comportamento e messaggi. Checkpoint: camera/input review + commit.

### 9.5 — Product lookup ed error handling

- Scope: GET prodotto, loading, successo, not-found, server/timeout/offline/parse error e retry controllato.
- Prerequisiti: 9.4; fixture prodotto nota e barcode assente; backend locale autorizzato.
- Casi positivi: mapping product/ingredients/allergens e navigazione dettaglio.
- Casi negativi: 404/logical not-found, 4xx/5xx, body invalido, timeout, rete persa, doppia richiesta.
- Device/manual: messaggi leggibili, nessuna risposta grezza, recupero a Home/scanner.
- Automatici: client/provider contract tests con fake response e negative corpus.
- Evidenza: status e safe code, evento sanitizzato; mai response body raw.
- PASS: stati distinti e nessun dato inventato. FAIL: eccezione/raw body in UI/log, not-found trattato come prodotto, fallback cache non dichiarato.
- Stop/difetti/approvazione: raw payload/leakage=`CRITICAL`; lookup MVP inutilizzabile=`HIGH`. Product owner approva stati/error copy. Checkpoint: API contract review + commit.

### 9.6 — Dettaglio prodotto e semantica score/evaluability

- Scope: info prodotto, ingredienti, nutrizione, allergeni, avvisi informativi, componenti separati, zero, `not_computable`, `non_applicable`, overall deferred/unavailable.
- Prerequisiti: 9.5; fixture tipizzate e vincoli Phase 7/8 congelati; nessuna esecuzione scoring.
- Casi positivi: valore computabile incluso zero; stati non numerici distinti; coverage/confidence/missing/uncertainty separati; overall senza numero.
- Casi negativi: campo assente/null/stringa, valori fuori range, score legacy/placeholder, media client, nutrizione parziale, allergene personale.
- Device/manual: leggibilità, neutralità di colori/copy, disclaimer informativo/non-medico, screen reader.
- Automatici: model/widget/golden contract tests; fail-closed su combinazioni vietate.
- Evidenza: fixture ID, screenshot revisionato, assertion di assenza overall/fallback.
- PASS: semantica preservata e claim conformi. FAIL: missing→0/media, overall numero/band, sicurezza/idoneità personale, componenti fusi.
- Stop/difetti/approvazione: semantica/claim vietato=`CRITICAL/HIGH`. Product owner e governance owner approvano separatamente copy e stati. Checkpoint: semantic/governance review + commit.

### 9.7 — Creazione prodotto, camera/galleria/crop/OCR

- Scope: form, validazione food-only, foto prodotto/ingredienti/nutrizione, camera/galleria, crop, OCR locale e creazione.
- Prerequisiti: 9.6; immagini fixture non sensibili; percorso legacy isolato/disabilitato o caso dichiarato bloccato; backend locale autorizzato.
- Casi positivi: cancel/select/crop, OCR locale, correzione manuale, numeri con punto/virgola, submit unico e conferma.
- Casi negativi: permessi negati, foto vuota/illeggibile, crop fallito/cancellato, non-food/cosmetico, campi richiesti assenti, valori invalidi, barcode duplicato, rete persa.
- Device/manual: camera e gallery reali, tastiera, form lungo, rotazione/background durante picker/crop.
- Automatici: validator/parser/widget/client contract; mock OCR; nessun provider esterno.
- Evidenza: soli metadati allowlisted e comportamento UI; mai immagine/base64/OCR raw.
- PASS: flow food-only sicuro senza `/analyze-image`, placeholder score o raw logging. FAIL: i controlli ordinari continuano sul legacy, inseriscono `50/80/65`, marcano verificato o inviano base64 come percorso canonico.
- Stop/difetti/approvazione: legacy/scoring/claim verified=`CRITICAL/HIGH`. Product owner approva scope e campi. Checkpoint: form/privacy/backend contract review + commit.

### 9.8 — Canonical mobile upload/finalize/extraction E2E

- Scope: pannello dev, token memory-only, metadati, initialize, PUT esatto, finalize, start/list/get extraction, retry/idempotenza.
- Prerequisiti: 9.1, 9.2 e product ID fixture; facade default-off abilitata solo localmente; storage/extraction fake locali; host raggiungibili.
- Casi positivi: sequenza completa per ingredients e nutrition; product_front termina senza extraction; list/get coerenti.
- Casi negativi: token mancante/scaduto, ID/barcode mismatch, MIME/size/hash errati, capability scaduta, PUT/finalize/extraction 4xx/5xx/timeout, purpose unsupported, run ID errato.
- Device/manual: camera/gallery/crop del pannello, stati e pulsanti, retry massimo controllato, copy/clear log.
- Automatici: gateway/controller/facade/contract/idempotency/sanitizer tests e fake storage/provider.
- Evidenza: timeline sanitizzata con ID sicuri, status, latenza, retry e item count; niente URL/body/testo raw.
- PASS: una catena canonica completa e correlabile per caso, nessuna route legacy/scoring. FAIL: qualunque step mancante, ID confusi o fallback.
- Stop/difetti/approvazione: legacy/leakage/bypass=`CRITICAL`; E2E rotto=`HIGH`. Product owner approva il risultato E2E, security owner le evidenze. Checkpoint: E2E review + commit.

### 9.9 — History, cache e persistence

- Scope: storico in memoria, recent scans Home, Hive cache/history, ordine/limite/rimozione/clear e restart.
- Prerequisiti: 9.5; schema di persistenza autorizzato; dati fixture; decisione privacy/retention.
- Casi positivi: inserimento una volta, ordine recente, apertura dettaglio, restart e clear coerenti.
- Casi negativi: deserializzazione invalida/versione vecchia, duplicati, record mancanti, storage pieno/corrotto, immagine/base64 in history.
- Device/manual: background/kill/restart, upgrade simulato, clear data, modalità offline dichiarata.
- Automatici: serialization round-trip/migration/repository/provider/widget; limiti e corruption handling.
- Evidenza: conteggi/ID sintetici e UI, non contenuto memorizzato.
- PASS: fonte unica coerente e privacy approvata. FAIL: UI in-memory discordante da Hive, `UnimplementedError`, dati persi/sintetizzati, Home sempre placeholder.
- Stop/difetti/approvazione: perdita/corruzione=`CRITICAL/HIGH`; incoerenza=`HIGH/MEDIUM`. Product owner approva retention/offline semantics. Checkpoint: data/privacy review + commit.

### 9.10 — Settings e classificazione MVP/deferred

- Scope: settings shell, Premium, paese, allergie, lingua, Privacy, Terms e logout; decidere retain/remove/defer.
- Prerequisiti: inventario 9.0 e decisione prodotto; testi legali disponibili per eventuali link reali.
- Casi positivi: soltanto funzioni approvate sono operative; deferred/demo sono chiaramente non disponibili o rimosse.
- Casi negativi: toggle abilita capacità inesistente, paese influenza fact-check non implementato, allergie implicano idoneità, lingua non localizza, link placeholder, logout finto.
- Device/manual: ogni controllo, restart, accessibilità e coerenza copy.
- Automatici: provider/widget/localization/link tests dopo decisione; nessuna auth simulata come reale.
- Evidenza: decision record per ciascuna feature, screenshot revisionato, approvazione owner.
- PASS: nessun controllo promette capacità inesistente o personalizzazione sanitaria. FAIL: demo visibile come MVP o claim eccedente.
- Stop/difetti/approvazione: consiglio/idoneità/legale ingannevole=`CRITICAL/HIGH`. Product owner decide ogni feature; legal/privacy owner approva documenti. Checkpoint: scope/legal review + commit.

### 9.11 — Resilience, security, privacy e negative testing

- Scope: timeout/offline/retry, auth/token, input ostile, logging, screenshot/clipboard cleanup, default-off e assenza legacy.
- Prerequisiti: 9.1–9.10 pertinenti; threat cases e retry budget concordati.
- Casi positivi: fail-closed, errori sicuri, clear token/log/clipboard, recupero senza duplicazioni.
- Casi negativi: secret injection, URL/query, body enorme/malformato, redirect, header proibiti, token replay/scaduto, rete flapping, response/provider text ostile.
- Device/manual: airplane mode, cambio rete, background, permessi, clipboard e schermate recenti OS.
- Automatici: negative/security contract tests, secret scan, log corpus, auth/idempotency e redirect tests.
- Evidenza: report sintetico per categoria e safe code; nessun exploit payload raw nel pacchetto.
- PASS: nessun leakage/bypass/fallback e failure recuperabili. FAIL: contenuto vietato, retry illimitato, default-on, autenticazione aggirabile.
- Stop/difetti/approvazione: security/privacy failure=`CRITICAL`; resilience primaria=`HIGH`. Security/privacy owner e product owner firmano il gate. Checkpoint: security review + commit.

### 9.12 — Accessibility, performance, lifecycle e device compatibility

- Scope: screen reader, focus/tap target/contrast/text scale, startup e latenza UI, memoria, rotation/background/resume, matrice device/OS.
- Prerequisiti: flussi funzionali stabili; device rappresentativi concordati; budget misurabili.
- Casi positivi: flussi completi con assistive tech, text scale, lifecycle e device minimi.
- Casi negativi: font grande, contrasto, screen reader order, interruzione picker/upload, low memory, rete lenta, device senza camera.
- Device/manual: almeno device/OS minimi approvati; cold/warm start, background/resume/kill e orientamento.
- Automatici: semantics/widget checks, static accessibility scan e benchmark ripetibili dove disponibili.
- Evidenza: device matrix, tempi aggregati non sensibili, issue IDs e screenshot revisionati.
- PASS: nessun blocker accessibilità/lifecycle/performance; budget product owner rispettati. FAIL: percorso primario inaccessibile, stato corrotto o freeze.
- Stop/difetti/approvazione: inaccessibilità primaria/crash=`HIGH`; regressioni minori=`MEDIUM/LOW`. Product owner approva device matrix e budget. Checkpoint: compatibility review + commit.

### 9.13 — Full regression, UX/governance checkpoint e report finale

- Scope: regression completa delle feature MVP, closure difetti, audit evidenze/claim/docs e report Phase 9.
- Prerequisiti: 9.1–9.12 completate o defer autorizzati; commit candidato congelato; matrice aggiornata.
- Casi positivi: tutti i mandatory case ripetuti sul candidato; upgrade/restart e catena canonica; evidenza collegata.
- Casi negativi: regression dei difetti critical/high, assenza legacy/scoring, missing/zero, privacy/logging e claim.
- Device/manual: journey completi sulla matrice device approvata e review UX finale.
- Automatici: suite unit/widget/integration/backend autorizzata, link/secrets/diff checks e artifact audit.
- Evidenza: matrice firmata, defect closure, report Phase 9, commit/device/OS, approval date.
- PASS: criteri `ACCEPTED` soddisfatti per ogni feature MVP e nessun critical/high. FAIL: caso obbligatorio non PASS, evidenza mancante o owner non approva.
- Stop/difetti/approvazione: qualsiasi regressione critical/high ferma il gate. Product owner dà approvazione finale per Phase 9; produzione/release restano comunque non autorizzate. Checkpoint: final review e commit/report separatamente autorizzati.

## 5. Logging gap analysis

| Capacità | Stato repository | Gap/azione 9.1 |
| --- | --- | --- |
| Eventi frontend strutturati sanitizzati | Presente solo per percorso mobile dev, in memoria, max 200, copia/clear | Estendere l'orchestrazione a session/test ID senza includere dati raw; validare sul device |
| Summary backend sicuri | Presente per eventi `mobile_facade` con campi allowlisted | Non esiste export guidato; l'operatore deve ancora estrarre e revisionare manualmente |
| Correlation ID cross-layer completo | Parziale: `X-Request-ID` per ogni control-plane call | Nessun unico ID attraversa intero flow e PUT storage; introdurre correlation/session ID sicuro end-to-end |
| Secret scanning automatico | Assente | Scanner fail-closed sul pacchetto finale e corpus negativo |
| Unico feedback package sanitizzato | Assente | Generatore one-command/wizard con schema `WYE_PHASE_9_FEEDBACK_V1` |

Il legacy `ApiClient` registra barcode/nome, payload di `/analyze`, response body di lookup e `/analyze-image`, error body ed eccezioni; `AddProductScreen` registra oggetti normalizzati e stack trace. Quell'output non è sicuro da incollare. La Phase 9.1 deve produrre evidenza indipendente dal terminale raw, non etichettare retroattivamente come “safe” i log legacy.

## 6. Documentation authority audit

| Documento/gruppo | Classificazione | Uso Phase 9 |
| --- | --- | --- |
| `WYE_PHASE_9_APP_ACCEPTANCE_PLAN.md`, matrice, feedback guide, transition | `authoritative` | Scope, esecuzione, stato ed evidenza Phase 9 |
| `WYE_PHASE_7_COMPLETION_REPORT.md` e RFC Phase 7 richiamati | `authoritative` | Vincoli prodotto/governance; non autorizzano runtime |
| `WYE_PHASE_8_MOBILE_E2E_500_POSTMORTEM.md` | `authoritative` | Evidenza storica del fallimento legacy |
| `WYE_PHASE_8_FRONTEND_PLAN.md`, capture/upload flow/implementation e facade decision | `partially authoritative` | Baseline tecnica e decisioni storiche; roadmap 8.7/8.8 superseded dalla transition |
| Runbook, log template e `WYE_MOBILE_E2E_SELF_TEST_GUIDE.md` | `partially authoritative` | Solo dettagli tecnici canonical dev E2E; il piano/feedback Phase 9 prevalgono |
| `wye-flutter/README.md`, `wye-flutter/START_HERE.md`, `wye-flutter/QUICK_START.md` | `unsafe for current Phase 9 acceptance` | Contengono overall numerici, salubrità/cosmetici, premium/personale o procedure obsolete |
| `wye-flutter/TESTING_GUIDE.md`, `wye-flutter/TESTING_COMPLETE_GUIDE.md` | `unsafe for current Phase 9 acceptance` | Attese score/finale, premium/allergie e dichiarazioni di completezza non valide |
| `wye-flutter/ARCHITECTURE.md`, `wye-flutter/DOCS_INDEX.md` | `legacy` | Descrivono scoring/personalizzazione/production readiness e componenti non correnti |
| `how_to_start.md`, `test_smartphone_steps.md`, `Checkpoints/Step_manuale/test_images_backend_steps.md`, `fix_frontend.md` | `legacy` | Appunti storici; non sono runbook Phase 9 e possono invocare percorsi non autorizzati |
| Checkpoint Phase 1–6 e guide DB | `superseded` per acceptance app | Conservano storia tecnica; non determinano accettazione Phase 9 |

I documenti legacy non vengono riscritti in 9.0. Ogni futura procedura deve linkare esplicitamente i documenti autorevoli sopra.

## 7. Gate finale Phase 9

Phase 9 può essere dichiarata completata soltanto con matrice tracciabile, report finale e approvazioni. Anche in quel caso il risultato autorizza al massimo la conclusione dell'accettazione locale/dev MVP: non autorizza scoring runtime, produzione, certificazione esterna, pubblicazione negli store o release.
