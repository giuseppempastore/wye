# WYE — Phase 9 Feature Acceptance Matrix

## 1. Regole della matrice

Baseline di inventario: `b226a4ac6730378af828b7a86e1d2d7967ce86b6`. Gli stati di classificazione ammessi sono `MVP_REQUIRED`, `IMPLEMENTED_UNVERIFIED`, `LEGACY_BLOCKED`, `DEMO_ONLY`, `DEFERRED`, `OUT_OF_SCOPE`, `ACCEPTED`. Gli esiti ammessi sono `NOT_RUN`, `PASS`, `FAIL`, `BLOCKED`, `DEFERRED`, `OUT_OF_SCOPE`, `ACCEPTED`.

In questa Phase 9.0 nessuna voce è `ACCEPTED`. Una voce può diventarlo soltanto quando tutti i casi obbligatori sono `PASS`, non resta alcun blocker critical/high, esiste evidenza sanitizzata, i vincoli Phase 7/8 sono rispettati, non avviene alcun fallback legacy/scoring non autorizzato e il product owner registra approvazione e data.

Legenda test: `S` statico/automated, `W` widget/unit, `B` backend contract, `D` device/manual, `E` end-to-end, `N` negative/resilience, `A11Y` accessibilità, `G` governance/copy. L'evidenza non include mai segreti, URL firmati completi, immagini/base64, OCR/provider text o payload/log/traceback raw.

## 2. Inventario e classificazione

| Feature ID | Screen/route | User goal | Implementation location | Backend dependency | Current implementation state | MVP status | Required test type | Expected evidence | Known risk | Approval owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APP-START-001 | app startup | Avviare WYE e arrivare alla Home | `lib/main.dart`, `DatabaseService.init` | Hive locale | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | S,W,D,N | cold/warm start, stato UI, safe error | Hive init blocca `runApp`; nessuna recovery | Product owner |
| APP-HEALTH-001 | integration-facing | Conoscere raggiungibilità backend | `ApiClient.healthCheck`, `AppStateProvider` | `GET /health` | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,B,D,N | connected/offline state sicuro | health e `initApp` non risultano collegati alla UI | Product owner |
| HOME-SHELL-001 | `/` | Vedere identità app e azioni principali | `home_screen.dart` | Nessuna | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,A11Y | screenshot revisionato, tap map | Asset/layout non provati su device | Product owner |
| HOME-INFO-001 | `/` | Capire lo scopo informativo | `HomeScreen` expansion | Nessuna | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | D,A11Y,G | copy review e screen reader | Disclaimer non-medico non completo | Product + governance owner |
| HOME-RECENT-001 | `/` | Vedere scansioni recenti | placeholder `HomeScreen` | Provider/history futuro | DEMO_ONLY | MVP_REQUIRED | W,D,E | lista reale/empty state | Mostra sempre empty placeholder | Product owner |
| NAV-BOTTOM-001 | shell | Navigare Home/Storico/Settings | bottom bars nelle screen | Nessuna | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,A11Y | route per ogni tap/back | currentIndex incoerente nelle route secondarie | Product owner |
| NAV-ROUTES-001 | tutte | Aprire CTA e deep link previsti | `app_router.dart` | Lookup per dettaglio | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,N | route table e recupero | Parametro barcode non validato nel router | Product owner |
| NAV-404-001 | route ignota | Recuperare da URL non valido | `GoRouter.errorBuilder` | Nessuna | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D | 404 + ritorno Home | Nessun dettaglio/accessibility test | Product owner |
| BAR-CAMERA-001 | `/scanner` | Scansionare un barcode con camera | `BarcodeScannerScreen`, `mobile_scanner` | `/product/{barcode}` | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,E,N | singola detection e lookup | permessi/error text raw, device unverified | Product owner |
| BAR-DEBOUNCE-001 | `/scanner` | Evitare lookup duplicate | `_shouldProcessBarcode` | `/product/{barcode}` | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,N | request count sintetico | filtro solo lunghezza >=8, no checksum | Product owner |
| BAR-MANUAL-001 | `/scanner` | Inserire/cercare barcode manualmente | TextField + submit | `/product/{barcode}` | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,E,N | valid/empty/malformed | validazione minima | Product owner |
| BAR-ADD-SCAN-001 | `/add-product` | Precompilare barcode dal dialog camera | `_openBarcodeScanner` | Nessuna immediata | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | D,N,A11Y | dialog cancel/detect | lifecycle/permission non gestiti | Product owner |
| LOOKUP-001 | `/scanner`, `/product/:barcode` | Recuperare prodotto catalogo | provider + `ApiClient.getProductByBarcode` | `GET /product/{barcode}`, DB | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,B,D,E,N | status safe + dettaglio | response body/barcode loggati raw | Product + security owner |
| LOOKUP-NOTFOUND-001 | scanner/detail | Capire prodotto assente e recuperare | exception/provider/UI | stesso endpoint | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,B,D,N | not-found distinto, CTA sicura | copy rimanda a “Premium” non autorizzato | Product owner |
| DETAIL-SHELL-001 | `/product/:barcode` | Vedere identità e azioni prodotto | `product_detail_screen.dart` | lookup | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,E,A11Y | loading/success/error/back | ricarica rete da storico | Product owner |
| DETAIL-ING-001 | dettaglio | Consultare ingredienti | product mapper + section UI | DB ingredients | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,B,D,G | ordine e missing state | omissione silenziosa se lista vuota | Product + governance owner |
| DETAIL-NUT-001 | dettaglio | Consultare nutrizione separata | `NutritionFacts`, UI | DB nutrition contract | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,B,D,N | valori/missing distinti | lookup mapper non popola nutrition | Product + governance owner |
| DETAIL-ALLERGEN-001 | dettaglio | Vedere allergeni dichiarati | mapper + `AllergenBadge` | ingredient flags | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,B,D,G | badge e disclaimer | possibile implicazione di sicurezza/personale | Product + governance owner |
| DETAIL-NOTICE-001 | dettaglio | Vedere segnalazioni informative | `dangerousSubstances` + UI | legacy risk flags | LEGACY_BLOCKED | MVP_REQUIRED | S,W,D,G | copy neutro e provenienza | mappa “risky/dangerous”, claim vietato | Governance owner |
| SCORE-SEPARATE-001 | dettaglio/manuale | Vedere ingredienti e nutrizione separati | `ScoreCard` | typed score contract futuro | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,G | due componenti, nessuna fusione | runtime contract non connesso | Product + governance owner |
| SCORE-ZERO-001 | score card | Vedere zero computabile come `0 su 100` | models/widget + unit tests | typed fixture | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,N | assertion e screenshot | regressione zero→missing | Governance owner |
| SCORE-NC-001 | score card | Vedere `not_computable` senza numero | models/widget | typed fixture | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,N | neutral state, no number | fallback da legacy/null | Governance owner |
| SCORE-NA-001 | score card | Vedere `non_applicable` distinto | models/widget | typed fixture | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,N | label distinta, no number | confusione con errore/positivo | Governance owner |
| SCORE-SUPPORT-001 | score card | Vedere coverage/confidence/missing/uncertainty separati | `score_widgets.dart` | typed score contract | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,A11Y,G | valori separati | UI conta elementi ma non spiega dettagli | Product + governance owner |
| SCORE-OVERALL-001 | score card | Vedere overall non disponibile/differito | models/widget | Nessun runtime scoring | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,N,G | assenza numero/band/media | stale docs/backend espongono overall | Product + governance owner |
| MANUAL-ANALYSIS-001 | `/manual-analysis` | Inserire ingredienti manualmente | screen/provider/ApiClient | `POST /analyze`, scoring | LEGACY_BLOCKED | DEFERRED | S,W,N,G | prova di isolamento/disabilitazione | chiama scoring legacy e include cosmetici | Product + governance owner |
| MANUAL-SCROLL-001 | `/manual-analysis` | Raggiungere risultati automaticamente | `_scrollToResults` | Nessuna | DEMO_ONLY | DEFERRED | W,D | scroll osservabile | metodo vuoto | Product owner |
| ADD-FORM-001 | `/add-product` | Inserire/correggere dati food | `add_product_screen.dart` | `POST /products` | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,E,N,A11Y | validation e submit states | campi lunghi, regole incoerenti | Product owner |
| ADD-FOOD-SCOPE-001 | `/add-product` | Impedire categorie fuori packaged food | form e `_submit` | create product | LEGACY_BLOCKED | MVP_REQUIRED | W,D,N,G | non-food rifiutato | opzione `cosmetic` nel product type; AI decide category | Product + governance owner |
| CREATE-PRODUCT-001 | `/add-product` | Creare un prodotto | provider/ApiClient + `main.py` | DB products/ingredients/nutrition | LEGACY_BLOCKED | MVP_REQUIRED | B,D,E,N,G | 201/id sicuro e read-back | base64, `verified=True`, placeholder scores 50/80/65 | Product + governance owner |
| PHOTO-CAMERA-001 | add-product | Acquisire foto con camera | `ImagePicker` | poi legacy/canonical secondo controllo | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | D,N | select/cancel/permission | controllo ordinario prosegue a legacy | Product + security owner |
| PHOTO-GALLERY-001 | add-product | Scegliere immagine locale | `ImagePicker` | poi legacy/canonical | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | D,N | select/cancel/limited access | privacy e lifecycle non provati | Product + security owner |
| PHOTO-CROP-001 | add-product/dev panel | Ritagliare o annullare | `ImageCropper` | Nessuna | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | D,N,A11Y | crop/cancel/fallback | error/stack log raw nel flow ordinario | Product owner |
| OCR-LOCAL-001 | add-product | Estrarre testo localmente | ML Kit `TextRecognizer` | Nessuna per OCR | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | D,N | campi precompilati, no raw evidence | raw OCR inviato poi a provider legacy | Product + privacy owner |
| LEGACY-PHOTO-001 | add-product foto ordinarie | Analizzare foto | `_extractTextFromPhoto`/ApiClient | `POST /analyze-image`, OpenAI | LEGACY_BLOCKED | OUT_OF_SCOPE | S,D,N | prova che non è invocato | primo device run HTTP 500; base64/raw logs | Product + security owner |
| LEGACY-NORMALIZE-001 | client non visibile diretto | Normalizzare OCR | `normalizePhotoText` | `POST /normalize-photo` | DEFERRED | DEFERRED | S,B,N | decision record | raw OCR payload; non usato dal flow corrente | Product + privacy owner |
| MOB-PANEL-001 | `/add-product` flag on | Usare percorso canonico dev | `DevMobileCaptureUploadPanel` | mobile facade | IMPLEMENTED_UNVERIFIED | DEMO_ONLY | W,D,E,A11Y | pannello e stato default-off | confondibile con foto ordinarie | Product owner |
| MOB-TOKEN-001 | `/settings` flag on | Impostare/rimuovere token temporaneo | token panel/provider | session creata fuori app | IMPLEMENTED_UNVERIFIED | DEMO_ONLY | W,D,N | masked/memory-only/expiry/clear | clipboard/operator transfer | Security owner |
| MOB-INIT-001 | dev panel | Inizializzare upload | gateway/controller | facade initialize + storage | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,B,D,E,N | request ID/status/latency safe | device/LAN unverified | Product + security owner |
| MOB-PUT-001 | dev panel | Inviare byte esatti | HTTP gateway | presigned storage PUT | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,B,D,E,N | status/latency, hash contract | nessun request ID condiviso; URL sensibile | Security owner |
| MOB-FINAL-001 | dev panel | Finalizzare e associare immagine | gateway/controller | facade finalize + DB/storage | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,B,D,E,N | safe image/storage IDs | retry/idempotenza su device | Product + security owner |
| EXT-START-001 | dev panel | Avviare estrazione label | controller/gateway/UI | facade extraction POST | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,B,D,E,N | run ID/status safe | provider deve restare fake locale | Product + security owner |
| EXT-LIST-001 | integration-facing | Elencare extraction run | gateway | facade extraction GET list | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,B,E,N | run count/IDs safe | nessun controllo UI esplicito usa list | Product owner |
| EXT-GET-001 | dev panel | Aggiornare/leggere extraction run | refresh/gateway | facade extraction GET | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,B,D,E,N | state/items allowlisted | normalized text in UI richiede privacy review | Product + privacy owner |
| FLOW-RETRY-001 | dev panel | Riprovare failure temporanee | controller/UI | facade/storage/extraction | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,B,D,E,N | retry_count e idempotenza | nessun budget UI esplicito | Product + security owner |
| FLOW-ERROR-001 | dev panel | Distinguere retryable/terminal/unavailable | state models/UI | safe errors facade | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,N,A11Y | safe code e stato | errore generico, recovery incompleta | Product owner |
| LOG-FRONT-001 | dev panel | Vedere/copiare/svuotare eventi sicuri | logger + log panel | Nessuna | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,N | export allowlisted e clear | solo flow canonico, in memoria | Security + privacy owner |
| LOG-BACK-001 | backend mobile facade | Ottenere summary sicuri | `_log_transition` | logging backend | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | B,E,N | campi allowlisted | estrazione manuale dal terminale | Security owner |
| LOG-CORR-001 | cross-layer | Correlare una sessione completa | request IDs per call | facade + storage | DEFERRED | MVP_REQUIRED | B,E,N | unico correlation graph | PUT e operazioni hanno ID distinti | Security owner |
| LOG-PACKAGE-001 | operatore | Generare unico feedback sanitizzato | non presente | frontend/backend evidence | DEFERRED | MVP_REQUIRED | W,B,D,N | package + secret scan | oggi assemblaggio manuale | Security + product owner |
| HISTORY-MEM-001 | `/history` | Vedere scansioni della sessione | provider list max 50 | lookup al tap | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,E,N | order/count/open | perde tutto al restart | Product owner |
| HISTORY-HOME-001 | `/` | Vedere recenti anche in Home | placeholder | history provider | DEMO_ONLY | MVP_REQUIRED | W,D,E | stessi record dello storico | nessun wiring | Product owner |
| CACHE-HIVE-001 | startup/service | Salvare e recuperare cache/storico | `database_service.dart` | Hive | LEGACY_BLOCKED | MVP_REQUIRED | W,D,N | round-trip/restart/corruption | `Map.toString`, deserializzazione non implementata | Product + privacy owner |
| SETTINGS-SHELL-001 | `/settings` | Consultare impostazioni e info app | `settings_screen.dart` | Nessuna | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,D,A11Y | ogni controllo e nav | stato solo memoria | Product owner |
| SETTINGS-VERSION-001 | `/settings` | Conoscere versione installata | testo hardcoded `1.0.0` | package metadata assente | DEMO_ONLY | MVP_REQUIRED | S,W,D | confronto build/versione UI | valore può divergere dalla build | Product owner |
| SETTINGS-PREMIUM-001 | `/settings` | Attivare Premium | provider/switch/button | nessuna entitlement | DEMO_ONLY | DEFERRED | W,D,N,G | decision record | abilita feature senza auth/pagamento | Product owner |
| SETTINGS-COUNTRY-001 | settings/scanner | Scegliere paese | provider/dropdown | nessun fact-check reale | DEMO_ONLY | DEFERRED | W,D,G | decision record | promette fact checking/personalizzazione | Product + governance owner |
| SETTINGS-ALLERGY-001 | settings/detail | Salvare allergie ed evidenziare badge | provider/UI | ingredient flags | LEGACY_BLOCKED | DEFERRED | W,D,N,G | decision/privacy record | implica suitability personale/medica | Product + governance owner |
| SETTINGS-LANG-001 | `/settings` | Scegliere lingua | provider/dropdown | nessuna localization | DEMO_ONLY | DEFERRED | W,D,A11Y | UI tradotta integralmente | cambia stato ma non copy app | Product owner |
| SETTINGS-PRIVACY-001 | `/settings` | Aprire Privacy Policy | gesture + SnackBar | documento/link assente | DEMO_ONLY | MVP_REQUIRED | W,D,A11Y,G | policy approvata e link reale | placeholder legale | Product + privacy owner |
| SETTINGS-TERMS-001 | `/settings` | Aprire Terms | gesture + SnackBar | documento/link assente | DEMO_ONLY | MVP_REQUIRED | W,D,A11Y,G | terms approvati e link reale | placeholder legale | Product + legal owner |
| SETTINGS-LOGOUT-001 | `/settings` | Uscire dall'account | demo SnackBar | auth assente | DEMO_ONLY | OUT_OF_SCOPE | W,D,G | controllo rimosso/decisione | promette account/logout inesistente | Product owner |
| MOCK-API-001 | test-only | Usare dati deterministici nei test | `mock_api_client.dart` | Nessuna | DEMO_ONLY | OUT_OF_SCOPE | S,W,N | fixture senza overall runtime | score componenti demo possono essere scambiati per dati approvati | Governance owner |
| CONSUMPTION-001 | model/docs only | Tracciare consumi/frequenza | classi `Consumption*`, vecchia architecture | backend assente | DEMO_ONLY | OUT_OF_SCOPE | S,G | decision record di esclusione | dose/frequenza/personalizzazione vietate | Product + governance owner |
| NET-OFFLINE-001 | tutti i flow rete | Capire e recuperare da offline/timeout | ApiClient + gateway error mapping | backend/storage | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | W,B,D,N | state/safe code/retry | legacy mostra eccezioni/body e copy adb | Product + security owner |
| LIFE-RESTART-001 | app | Conservare solo stato autorizzato al restart | provider/Hive/token/logger | Hive; token none | DEFERRED | MVP_REQUIRED | D,E,N | restart matrix | history/preferences persi, Hive rotto | Product + privacy owner |
| LIFE-BACKGROUND-001 | picker/upload/app | Gestire background/resume/interruzioni | nessun observer esplicito | rete/storage | DEFERRED | MVP_REQUIRED | D,E,N | state transition | token/scanner/picker/upload lifecycle ignoto | Product owner |
| PERM-CAMERA-001 | scanner/camera | Concedere, negare e recuperare permesso | plugins + Android manifest | OS | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | D,N,A11Y | permission matrix | iOS usage descriptions assenti; error raw | Product + privacy owner |
| PERM-GALLERY-001 | photo selection | Gestire accesso foto pieno/limitato/negato | plugins + Android manifest | OS | IMPLEMENTED_UNVERIFIED | MVP_REQUIRED | D,N,A11Y | permission matrix | iOS usage descriptions assenti | Product + privacy owner |
| A11Y-APP-001 | tutte | Usare l'app con tecnologie assistive | widget standard, pochi tooltip | Nessuna | DEFERRED | MVP_REQUIRED | D,A11Y,W | screen reader/focus/scale/contrast | nessun audit sistematico/Semantics | Product owner |
| PERF-DEVICE-001 | tutti i journey | Usare app senza freeze/lag anomalo | intera app | backend/storage locali | DEFERRED | MVP_REQUIRED | D,E,N | tempi aggregati e device matrix | base64/OCR/memoria immagini | Product owner |

## 3. Registro iniziale dei casi e dell'accettazione

Tutti i casi obbligatori partono non eseguiti o bloccati dall'evidenza statica. `approval date` resta vuota finché il product owner non firma; un'approvazione futura deve riferirsi al commit completo a 40 caratteri.

| Feature ID | Test-case IDs | Current result | Evidence reference | Defect IDs | Last tested commit | Device/OS | Approval owner | Approval date | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APP-START-001…NAV-404-001 | `TC-9.02-START-01..04`; `TC-9.03-SHELL-01..04` | NOT_RUN | — | — | — | — | Product owner | — | Includes health/connectivity static gap |
| BAR-CAMERA-001…BAR-ADD-SCAN-001 | `TC-9.04-BAR-01..08` | NOT_RUN | — | — | — | — | Product owner | — | Physical camera required |
| LOOKUP-001…DETAIL-NUT-001 | `TC-9.05-LOOK-01..09`; `TC-9.06-DET-01..03` | NOT_RUN | — | — | — | — | Product owner | — | Raw legacy client logs are not evidence |
| DETAIL-ALLERGEN-001 | `TC-9.06-ALL-01..03` | NOT_RUN | — | — | — | — | Product + governance owner | — | Claim review required |
| DETAIL-NOTICE-001 | `TC-9.06-NOT-01..03` | BLOCKED | `WYE_PHASE_8_FRONTEND_PLAN.md` | `D9-GOV-001` | — | — | Governance owner | — | Legacy risk/danger semantics |
| SCORE-SEPARATE-001…SCORE-OVERALL-001 | `TC-9.06-SCORE-01..12` | NOT_RUN | Phase 8 local tests (historical) | — | — | — | Product + governance owner | — | Local tests do not equal device acceptance |
| MANUAL-ANALYSIS-001 | `TC-9.10-MAN-01..03` | BLOCKED | static route inspection | `D9-LEG-001` | — | — | Product + governance owner | — | Calls `/analyze` scoring |
| MANUAL-SCROLL-001 | `TC-9.10-MAN-04` | DEFERRED | static inspection | `D9-DEMO-001` | — | — | Product owner | — | Empty method |
| ADD-FORM-001 | `TC-9.07-FORM-01..10` | NOT_RUN | — | — | — | — | Product owner | — | Device/form testing required |
| ADD-FOOD-SCOPE-001 | `TC-9.07-SCOPE-01..04` | BLOCKED | static inspection | `D9-GOV-002` | — | — | Product + governance owner | — | Conflicting cosmetic option |
| CREATE-PRODUCT-001 | `TC-9.07-CREATE-01..08` | BLOCKED | static backend inspection | `D9-LEG-002` | — | — | Product + governance owner | — | Placeholder score/verified/base64 behavior |
| PHOTO-CAMERA-001…OCR-LOCAL-001 | `TC-9.07-MEDIA-01..12` | BLOCKED | 500 postmortem + static inspection | `D9-LEG-003` | — | — | Product + privacy owner | — | Ordinary controls enter legacy path |
| LEGACY-PHOTO-001 | `TC-9.11-LEGACY-01` | BLOCKED | `WYE_PHASE_8_MOBILE_E2E_500_POSTMORTEM.md` | `D9-LEG-003` | — | physical phone/OS unrecorded | Security owner | — | Historical HTTP 500; must not rerun |
| LEGACY-NORMALIZE-001 | `TC-9.10-LEGACY-02` | DEFERRED | static inspection | — | — | — | Product + privacy owner | — | Not current visible flow |
| MOB-PANEL-001…MOB-TOKEN-001 | `TC-9.08-PANEL-01..06` | NOT_RUN | Phase 8 local tests (historical) | — | — | — | Product + security owner | — | Dev-only/default-off |
| MOB-INIT-001 | `TC-9.08-UPL-01..03` | NOT_RUN | — | — | — | — | Product + security owner | — | Canonical device path unverified |
| MOB-PUT-001 | `TC-9.08-UPL-04..06` | NOT_RUN | — | — | — | — | Security owner | — | Never record presigned URL |
| MOB-FINAL-001 | `TC-9.08-UPL-07..09` | NOT_RUN | — | — | — | — | Product + security owner | — | Canonical device path unverified |
| EXT-START-001…EXT-GET-001 | `TC-9.08-EXT-01..10` | NOT_RUN | — | — | — | — | Product + privacy owner | — | Fake local provider only |
| FLOW-RETRY-001…FLOW-ERROR-001 | `TC-9.08-ERR-01..10`; `TC-9.11-NET-01..05` | NOT_RUN | — | — | — | — | Product + security owner | — | Bounded retry required |
| LOG-FRONT-001…LOG-BACK-001 | `TC-9.01-LOG-01..08` | NOT_RUN | Phase 8 local tests (historical) | — | — | — | Security + privacy owner | — | Needs real operator validation |
| LOG-CORR-001 | `TC-9.01-CORR-01..03` | BLOCKED | static gap analysis | `D9-LOG-001` | — | — | Security owner | — | No full cross-layer ID |
| LOG-PACKAGE-001 | `TC-9.01-PKG-01..08` | BLOCKED | static gap analysis | `D9-LOG-002` | — | — | Security + product owner | — | Generator absent |
| HISTORY-MEM-001 | `TC-9.09-HIST-01..06` | NOT_RUN | — | — | — | — | Product owner | — | Session only |
| HISTORY-HOME-001 | `TC-9.09-HOME-01..03` | BLOCKED | static inspection | `D9-HIST-001` | — | — | Product owner | — | Permanent placeholder |
| CACHE-HIVE-001 | `TC-9.09-CACHE-01..10` | BLOCKED | static inspection | `D9-DATA-001` | — | — | Product + privacy owner | — | Deserialization throws |
| SETTINGS-SHELL-001…SETTINGS-VERSION-001 | `TC-9.10-SET-01..05` | NOT_RUN | — | — | — | — | Product owner | — | Version must match installed build |
| SETTINGS-PREMIUM-001…SETTINGS-LANG-001 | `TC-9.10-DEF-01..12` | DEFERRED | static classification | `D9-DEMO-002` | — | — | Product + governance owner | — | Demo/personalization not approved |
| SETTINGS-PRIVACY-001…SETTINGS-TERMS-001 | `TC-9.10-LEGAL-01..04` | BLOCKED | static inspection | `D9-LEGAL-001` | — | — | Privacy/legal owner | — | Placeholder links |
| SETTINGS-LOGOUT-001 | `TC-9.10-LOGOUT-01` | OUT_OF_SCOPE | static inspection | — | — | — | Product owner | — | No consumer auth contract |
| MOCK-API-001…CONSUMPTION-001 | `TC-9.10-OOS-01..03` | OUT_OF_SCOPE | static inspection | — | — | — | Product + governance owner | — | Must not enter MVP runtime |
| NET-OFFLINE-001 | `TC-9.11-OFF-01..10` | NOT_RUN | — | — | — | — | Product + security owner | — | Test only after safe logging workflow |
| LIFE-RESTART-001…LIFE-BACKGROUND-001 | `TC-9.12-LIFE-01..10` | BLOCKED | static gap analysis | `D9-LIFE-001` | — | — | Product owner | — | Persistence/lifecycle work missing |
| PERM-CAMERA-001…PERM-GALLERY-001 | `TC-9.12-PERM-01..10` | BLOCKED | manifest inspection | `D9-PERM-001` | — | — | Product + privacy owner | — | iOS usage descriptions absent |
| A11Y-APP-001 | `TC-9.12-A11Y-01..12` | NOT_RUN | — | — | — | — | Product owner | — | No systematic baseline |
| PERF-DEVICE-001 | `TC-9.12-PERF-01..08` | NOT_RUN | — | — | — | — | Product owner | — | Budgets to approve |

## 4. Aggiornamento del registro

Ogni esecuzione aggiunge un record atomico con `test_session_id` nel defect/evidence register e aggiorna la riga senza cancellare la storia. `Last tested commit` è il commit realmente installato sul device, non quello ispezionato staticamente. `PASS` non comporta `ACCEPTED`; l'owner compila `Approval date` solo al gate previsto dal piano.
