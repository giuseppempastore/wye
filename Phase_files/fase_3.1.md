# WYE — Fase 3.1: Repository Hygiene

## Stato

**COMPLETATA**

Branch:

```text
ingredients_score
```

Commit di partenza:

```text
ae497b9d04aece787320893d70c5285feee6e60d
```

Commit finale:

```text
non ancora creato
```

La Fase 3.1 ha corretto un problema strutturale del repository: migliaia di file generati da Python e dal virtual environment erano accidentalmente tracciati da Git.

---

## 1. Obiettivo

Prima della Fase 4 era necessario ripulire il repository da artefatti che non appartengono al codice sorgente:

```text
backend/venv/
__pycache__/
*.pyc
```

Questi file:

- vengono generati automaticamente;
- non devono essere versionati;
- aumentano inutilmente le dimensioni del repository;
- producono migliaia di modifiche irrilevanti;
- rendono più difficile leggere i veri diff applicativi.

La Fase 3.1 ha quindi separato correttamente:

```text
codice sorgente
≠
ambiente virtuale / cache Python
```

---

## 2. `.gitignore`

È stato creato un `.gitignore` root con:

```text
backend/venv/
venv/
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.env
.env.*
!.env.example
!**/.env.example
```

Questo impedisce che gli artefatti Python e i file `.env` reali vengano accidentalmente aggiunti in futuro.

I file di esempio restano invece versionabili:

```text
.env.example
```

In particolare:

```text
backend/.env.example
```

continua a essere tracciato correttamente.

---

## 3. Rimozione dal tracking Git

Sono stati rimossi dall'indice Git:

```text
backend/venv           → 4.034 file
__pycache__            → 1.859 file
*.pyc                  → 1.859 file
```

Le categorie si sovrappongono.

Rimozioni uniche complessive:

```text
4.052 file
```

Distribuzione rilevata:

```text
1.841 cache erano dentro il virtualenv
18 cache erano esterne al virtualenv
```

Dopo la pulizia:

```text
TRACKED_VENV=0
TRACKED_PYCACHE=0
TRACKED_PYC=0
```

---

## 4. I file locali non sono stati cancellati

La pulizia è stata eseguita tramite:

```text
git rm --cached
```

Questo significa che i file sono stati rimossi dal controllo versione, non dal filesystem locale.

Verifica:

```text
file backend/venv prima: 4.034
file backend/venv dopo:  4.034
```

Il virtual environment locale continua quindi a esistere.

Git semplicemente non lo seguirà più.

---

## 5. Integrità del codice applicativo

La Fase 3.1 non ha modificato:

- migration;
- codice backend;
- test;
- requirements;
- logica della Fase 3;
- frontend.

Risultato:

```text
file applicativi eliminati: 0
cancellazioni inattese:     0
```

Le sole modifiche preparate sono:

```text
1 nuovo file .gitignore
4.052 artefatti rimossi dall'indice Git
```

---

## 6. Verifiche Git

Sono state eseguite:

```text
git diff --check
```

Risultato:

```text
OK
```

e:

```text
git diff --cached --check
```

Risultato:

```text
OK
```

Non sono stati rilevati errori di whitespace o problemi nei diff preparati.

---

## 7. Test

I test sono stati eseguiti tramite un virtual environment temporaneo esterno al repository.

Bytecode Python disabilitato durante il test.

Risultato:

```text
19 test eseguiti
19 passed
0 failed
0 errors
0 skipped
```

Sono stati verificati:

- constraint Fase 2.1;
- lifecycle Fase 2.1;
- downgrade protetto;
- re-upgrade;
- API immagini;
- cleanup upload orfani;
- checksum;
- validazione immagini;
- idempotenza;
- concorrenza PostgreSQL;
- Moto S3;
- signed PUT;
- signed GET.

La repository hygiene non ha quindi alterato il funzionamento delle Fasi precedenti.

---

## 8. Problema OpenAI/httpx

Il problema preesistente:

```text
Client.__init__() got an unexpected keyword argument 'proxies'
```

non è stato modificato.

Rimane fuori scope della Fase 3.1.

Dovrà essere affrontato prima o durante la preparazione della futura pipeline AI.

---

## 9. Stato Git da committare

La Fase 3.1 è pronta per essere committata.

Contenuto del commit:

```text
.gitignore                           → aggiunto
backend/venv/...                    → rimossi dal tracking
**/__pycache__/...                  → rimossi dal tracking
*.pyc                               → rimossi dal tracking
```

I file locali generati restano presenti e saranno ignorati nelle future esecuzioni.

Messaggio commit consigliato:

```text
Fase 3.1 - Clean generated Python artifacts from repository
```

Dopo il commit è possibile eseguire il push della branch:

```text
ingredients_score
```

---

## 10. Perché questa fase era importante

Prima:

```text
modifica Python
→ genera cache
→ Git vede migliaia di cambiamenti
```

Ora:

```text
modifica Python
→ genera cache
→ .gitignore la ignora
→ Git mostra solo il codice reale
```

Questo rende molto più leggibili e sicure le successive fasi di sviluppo.

---

## 11. Stato finale

```text
.gitignore                     ✅
backend/venv non tracciato     ✅
__pycache__ non tracciato      ✅
*.pyc non tracciati            ✅
.env.example preservato        ✅
virtualenv locale preservato   ✅
codice applicativo invariato   ✅
git diff --check               ✅
test                           ✅ 19/19
```

# ✅ FASE 3.1 COMPLETATA

---

## 12. Roadmap aggiornata

```text
Fase 1
Alembic e baseline
✅ COMPLETATA

Fase 2
Modello dati scientifico e provenance
✅ COMPLETATA

Fase 2.1
Data Integrity Hardening
✅ COMPLETATA

Fase 3
Object Storage e acquisizione immagini
✅ COMPLETATA

Fase 3.1
Repository Hygiene
✅ COMPLETATA

Fase 4
OCR / AI / parsing etichetta
⏳ PROSSIMA

Fase 5
Normalizzazione e review mapping
⏳ PIANIFICATA

Fase 6
EFSA / OpenFoodTox ingestion
⏳ PIANIFICATA

Fase 7
Scoring scientifico versionato
⏳ PIANIFICATA
```

---

## 13. Sintesi semplice

Il repository WYE ora contiene soltanto ciò che deve realmente essere versionato.

Virtual environment, cache Python e bytecode non vengono più tracciati.

Questo significa che dalla Fase 4 in poi i diff Git mostreranno principalmente le vere modifiche al progetto, rendendo più semplice capire cosa Codex sta aggiungendo o modificando.
