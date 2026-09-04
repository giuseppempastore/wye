# WYE — Guida Phase 9 per test e feedback sanitizzato

## 1. A chi serve e quali documenti seguire

Questa guida è destinata a un operatore non sviluppatore. Per i test Phase 9 sono autorevoli, in quest'ordine: `WYE_PHASE_9_APP_ACCEPTANCE_PLAN.md`, `WYE_PHASE_9_FEATURE_ACCEPTANCE_MATRIX.md`, questa guida e `WYE_PHASE_8_TO_9_TRANSITION.md`. Il runbook e il log template Phase 8 restano riferimenti tecnici parziali per il solo percorso mobile canonico; le vecchie guide Flutter non sono procedure di accettazione Phase 9.

Esegui soltanto la subfase autorizzata, un caso alla volta. Non attivare produzione, scoring, endpoint legacy o provider esterni.

## 2. Dove si trova il pannello dei log

Il pannello `Log tecnici sanitizzati` appare soltanto quando la build locale è stata avviata con il percorso mobile dev abilitato. Apri `Aggiungi Prodotto da Foto`, scorri fino alla card `Upload mobile locale`, quindi fino in fondo alla card. Espandi `Log tecnici sanitizzati`.

Il pannello riguarda esclusivamente il percorso canonico mobile dev. Non rende sicuri i log di `/analyze`, `/analyze-image`, la console Flutter completa o il terminale backend.

## 3. Copiare e svuotare in sicurezza

1. Termina il singolo caso e non ripeterlo oltre il limite indicato.
2. Espandi il pannello e controlla visivamente ogni riga.
3. Se vedi token, URL completo, query string, percorso file, testo OCR, payload o dati personali, non copiare: classifica `STOPPED` e avvisa il responsabile.
4. Premi `Copia`; incolla prima in un editor locale temporaneo e completa l'audit.
5. Conserva soltanto gli eventi minimi relativi al `test_case_id`.
6. Premi `Svuota` subito dopo aver registrato l'evidenza approvata.

## 4. Cosa si può e non si può condividere

Puoi incollare in ChatGPT/Codex: ID tecnici già sanitizzati, nomi evento allowlisted, classe di stato, codice HTTP, safe error code, conteggio retry, latenza, commit, modello device, versione OS, passaggi UI, comportamento atteso/reale e un riassunto backend già revisionato.

Non incollare mai: segreti o token; header Authorization/Cookie/API key; URL presigned completo o query/signature; immagini o base64; testo OCR/provider grezzo; payload/request/response body grezzi; dati personali; path locali; dump database; variabili ambiente; log completi; traceback non redatti; screenshot non revisionati.

I log completi di `flutter run` e backend non vanno incollati alla cieca perché il codice legacy può scrivere barcode, payload, response body, errori, stack trace, base64 o contenuto del provider. Il fatto che una riga provenga da un terminale locale non la rende sanitizzata.

## 5. Segnalare un problema alla volta

- Riparti dal test-case ID esatto presente nella matrice, per esempio `TC-9.08-UPL-04`.
- Descrivi un solo primo comportamento inatteso; non mescolare errori successivi.
- Indica l'ultimo passaggio UI esatto completato.
- Scrivi `expected` come comportamento osservabile richiesto e `actual` come ciò che hai davvero visto.
- Registra lo status HTTP solo se visibile in evidenza già sanitizzata; altrimenti scrivi `not_available`.
- Non indovinare error code, request ID o risultato.

## 6. Screenshot revisionati

Prima di allegare uno screenshot, ritaglialo al minimo utile e controlla ogni area: nessun token, URL, QR code, notifica, nome account, indirizzo, immagine etichetta, barcode reale non autorizzato o testo sensibile. Segna `screenshot_available: yes_reviewed` soltanto dopo il controllo; altrimenti usa `no` o `withheld_unsafe`.

## 7. Classificazione operatore

| Stato operatore | Uso |
| --- | --- |
| `PASS` | Il comportamento atteso si verifica e l'evidenza minima è completa e sanitizzata. Non significa `ACCEPTED`. |
| `FAIL` | Il caso è stato eseguito e il comportamento reale differisce dall'atteso. |
| `BLOCKED` | Un prerequisito o difetto noto impedisce di iniziare o completare il caso senza violare il piano. |
| `STOPPED` | È scattata una stop condition: possibile esposizione, route legacy/scoring, provider esterno, retry oltre limite, crash/errore grave o ambiente non autorizzato. Interrompi la sessione. |

`STOPPED` è uno stato di feedback operativo: nella matrice si registra `BLOCKED` o `FAIL` e si apre un defect, secondo la causa.

## 8. Struttura riutilizzabile obbligatoria

Compila senza aggiungere log grezzi:

```text
test_session_id:
test_case_id:
commit:
device:
os_version:
result:
exact_ui_step:
expected:
actual:
http_status:
safe_error_code:
frontend_sanitized_events:
backend_safe_summary:
retry_count:
screenshot_available:
forbidden_content_audit:
```

Valori assenti: usa `not_available` o `not_observed`, mai valori inventati. `forbidden_content_audit` deve dire almeno `passed` oppure `failed_stop`.

## 9. Pacchetto compatto da incollare in ChatGPT/Codex

Incolla soltanto:

```text
WYE_PHASE_9_FEEDBACK_V1
test_session_id: <safe-id>
test_case_id: <TC-id>
commit: <40-hex>
device: <modello generico>
os_version: <versione>
result: <PASS|FAIL|BLOCKED|STOPPED>
exact_ui_step: <un passaggio>
expected: <frase breve>
actual: <frase breve, redatta>
http_status: <numero|not_available>
safe_error_code: <allowlisted_code|not_available>
frontend_sanitized_events: <massimo le righe minime revisionate>
backend_safe_summary: <eventi/codici/ID sicuri, niente log raw>
retry_count: <numero>
screenshot_available: <yes_reviewed|no|withheld_unsafe>
forbidden_content_audit: <passed|failed_stop>
```

Non è richiesto né accettabile allegare log completi.

## 10. Pulizia dopo il test

1. Premi `Svuota` nel pannello.
2. Cancella dagli appunti token, eventi e testo temporaneo copiando una stringa innocua vuota o usando il comando sicuro del sistema.
3. Premi `Rimuovi token` nelle impostazioni dev e verifica lo stato `Token mancante`.
4. Chiudi l'app; il token e i log sono in memoria e non devono essere recuperati come evidenza persistente.
5. Elimina soltanto gli artefatti temporanei di test esplicitamente autorizzati.
6. Se un contenuto vietato è stato copiato, non inoltrarlo: registra `STOPPED`, informa il responsabile e segui la procedura di revoca/rotazione appropriata.

## 11. Limiti attuali del feedback automatico

Il repository produce eventi frontend strutturati sanitizzati per il percorso canonico e summary backend `mobile_facade` revisionabili. Non produce ancora un unico correlation ID end-to-end che attraversi initialize, PUT storage, finalize ed extraction; il PUT non condivide un request ID applicativo. Non esiste secret scanning automatico della sessione né un generatore di pacchetto unico.

La Phase 9.1 deve implementare, dopo autorizzazione separata, un comando o wizard che raccolga soltanto campi allowlisted, esegua secret scanning fail-closed, unisca le evidenze per session/test ID e generi il pacchetto compatto. Questa Phase 9.0 documenta il gap e non implementa il generatore.
