# WYE — Transizione dalla Phase 8 alla Phase 9

## 1. Stato e autorità

- Baseline esaminata: branch `ingredients_score`, commit `b226a4ac6730378af828b7a86e1d2d7967ce86b6`.
- Decisione: la Phase 8 diventa la baseline di implementazione e integrazione; non è dichiarata accettata soltanto perché il codice è stato implementato o verificato localmente.
- La Phase 9 è la fase sistematica di accettazione dell'app su dispositivo reale, validazione, risoluzione difetti e approvazione del product owner.
- Questa transizione non autorizza scoring runtime, servizi di produzione, distribuzione o release.

## 2. Vincoli di prodotto che continuano a valere

WYE MVP fornisce indicazioni generali, approssimative e informative su alimenti confezionati. Non è un medico e non fornisce consigli medici, clinici, terapeutici o dietetici personalizzati, né raccomandazioni su dose, porzione o frequenza. Non dichiara sicurezza, salubrità, conformità normativa, certificazione esterna o idoneità individuale. Un'eventuale validazione o certificazione esterna è futura, opzionale e assente.

Lo zero computabile resta distinto da `not_computable`; dati mancanti o non computabili non possono diventare zero, media, valore intermedio, placeholder o fallback. Copertura, confidenza, incertezza, missingness ed evaluability restano separati dai valori. Le valutazioni ingredienti e nutrizione restano separate. Il punteggio complessivo numerico rimane non disponibile/differito.

## 3. Cosa ha implementato la Phase 8

- Modelli Flutter tipizzati per `computable`, `not_computable`, `non_applicable`, zero computabile e overall non disponibile/differito.
- Widget neutri per mostrare separatamente ingredienti e nutrizione senza calcolare un overall nel client.
- Contratto e state machine capture/upload: metadati immagine, initialize, PUT binario degli stessi byte, finalize e identità separate.
- Facade FastAPI dev-only, disabilitata di default, con sessione Bearer temporanea in memoria e route upload/estrazione.
- Client Flutter dev-only, disabilitato di default, con token solo in memoria, upload, start/list/get extraction, retry ed error states.
- Eventi frontend strutturati e sanitizzati, ultimi 200 in memoria, con pannello `Log tecnici sanitizzati`, copia e svuota.
- Eventi backend `mobile_facade` con campi allowlisted e `X-Request-ID` per le singole richieste control-plane.
- Runbook E2E, modello di log, guida self-test e postmortem del primo tentativo su telefono.

La presenza di questi componenti non approva i controlli ordinari foto, `/analyze`, `/analyze-image`, scoring, personalizzazione, persistenza o release.

## 4. Cosa è stato verificato localmente

La documentazione Phase 8 registra verifiche locali e test automatici su modelli, widget di evaluability, metadati SHA-256/MIME, gateway, controller, sanitizzazione e facade backend. Registra inoltre smoke locali di storage Moto e health backend nell'ambiente E2E predisposto. Queste prove caratterizzano codice e contratti in ambiente locale; non costituiscono accettazione end-to-end dell'app su telefono.

## 5. Cosa resta non verificato su dispositivo fisico

- Avvio ripetibile dell'intero ambiente e raggiungibilità LAN di API e host storage dal telefono.
- Percorso canonico completo: pannello dev, initialize, PUT binario, finalize, start/list/get extraction e risultato UI.
- Fotocamera barcode, inserimento manuale, lookup, not-found, dettaglio e creazione prodotto reali.
- Camera/galleria/crop/OCR, permessi negati o limitati e gestione lifecycle/background/restart.
- Offline, timeout, perdita di rete, retry, idempotenza e recupero coerente.
- Storico/cache/persistenza, impostazioni, accessibilità, performance e compatibilità device/OS.
- Testo, gerarchia visiva, disclaimer e conformità dei claim ai vincoli Phase 7/8.

## 6. Primo tentativo telefono e failure legacy

Il primo tentativo su telefono ha avviato l'app, ma il controllo foto ordinario ha chiamato `ApiClient.analyzeProductImage` e la route legacy `/analyze-image`. La richiesta è terminata con HTTP 500 e `OpenAI BadRequest` nel provider esterno prima di entrare nella facade mobile canonica.

Non esiste quindi evidenza di initialize mobile, PUT, finalize, extraction o fallimento Moto per quel tentativo. Il percorso canonico mobile resta `NOT_RUN` su dispositivo reale. L'output terminale legacy grezzo non è evidenza sicura da incollare.

## 7. Trasferimento del lavoro 8.7 e 8.8

| Lavoro precedente | Nuova collocazione Phase 9 |
| --- | --- |
| 8.7 Integration hardening: contratti, auth boundary, errori, idempotenza, retry, accessibilità e test | 9.1, 9.8, 9.11 e 9.12 |
| 8.8 Final UX/checkpoint review: prodotto, governance, claim e disclosure | 9.6, 9.10 e 9.13 |

Il trasferimento include anche l'hardening residuo emerso dall'inventario: eliminazione o isolamento dei fallback legacy, persistenza reale, documenti obsoleti e pacchetto evidenze sanitizzato. I checkpoint review/commit restano checkpoint di ciascuna subfase, non nuove subfasi funzionali.

## 8. Gate di transizione

La Phase 8 è chiusa come baseline di implementazione/integration preparation, non come accettazione finale dell'app. L'autorità operativa passa a `WYE_PHASE_9_APP_ACCEPTANCE_PLAN.md`; lo stato per-feature è registrato in `WYE_PHASE_9_FEATURE_ACCEPTANCE_MATRIX.md`; il feedback dell'operatore segue `WYE_PHASE_9_TEST_FEEDBACK_GUIDE.md`.

Nessuna feature diventa `ACCEPTED` senza casi obbligatori superati, evidenza sanitizzata, assenza di blocker critical/high, rispetto dei vincoli di prodotto, assenza di fallback legacy/scoring non autorizzati e approvazione documentata del product owner.

## 9. Decision record

```text
phase_8_status: IMPLEMENTATION_INTEGRATION_BASELINE
phase_8_final_app_acceptance: NO
canonical_mobile_real_device_status: NOT_RUN
legacy_first_phone_attempt: HTTP_500_BEFORE_MOBILE_FACADE
former_phase_8_7_and_8_8: TRANSFERRED_TO_PHASE_9
phase_9_role: APP_ACCEPTANCE_VALIDATION_DEFECT_RESOLUTION_APPROVAL
scoring_runtime_authority: NONE
production_authority: NONE
release_authority: NONE
```
