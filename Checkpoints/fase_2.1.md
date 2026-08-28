# WYE — Fase 2.1: Data Integrity Hardening

## 1. Stato della fase

La **Fase 2.1 — Data Integrity Hardening** è stata implementata a livello di codice, ma la validazione completa su PostgreSQL **non è ancora conclusa**.

La migration e i relativi test sono stati creati, ma il runner ha correttamente impedito l'esecuzione contro il database predefinito perché non identificato come database di test isolato.

Al momento non risulta configurata la variabile:

```text
WYE_TEST_DATABASE
```

Di conseguenza non sono ancora stati verificati direttamente:

- upgrade PostgreSQL `0002 → 0003`;
- downgrade PostgreSQL `0003 → 0002`;
- constraint e trigger su database reale;
- test PostgreSQL di integrazione;
- test di concorrenza.

La branch verificata è:

```text
ingredients_score
```

Commit di partenza:

```text
d59bcac
```

---

## 2. Obiettivo della Fase 2.1

La Fase 2 aveva introdotto il modello dati necessario per:

- immagini prodotto;
- documenti etichetta;
- OCR/AI versionati;
- ingredienti normalizzati;
- mapping controllati;
- sostanze scientifiche;
- dataset e release;
- assessment scientifici.

Prima di costruire la pipeline applicativa della Fase 3, la Fase 2.1 rafforza le garanzie di integrità del database.

Il principio è:

```text
prima rendere impossibili gli stati incoerenti
→ poi costruire upload, OCR, AI e scoring
```

Questa fase non introduce nuove funzionalità utente.

---

## 3. File creati

Sono stati creati:

```text
backend/migrations/versions/0003_data_integrity_hardening.py
backend/tests/test_data_integrity_hardening.py
```

La migration precedente:

```text
0002_scientific_data_model.py
```

non viene modificata retroattivamente.

---

## 4. Migration introdotta

La nuova migration è:

```text
0003_data_integrity_hardening
```

Il suo scopo è rafforzare il modello introdotto dalla Fase 2 senza perdere dati e senza correggere automaticamente situazioni ambigue.

La migration include un **preflight transazionale**.

Prima di applicare modifiche restrittive, verifica la presenza di dati incompatibili.

Se trova una situazione che non può essere risolta deterministicamente, la migration deve interrompersi invece di inventare una correzione.

Schema concettuale:

```text
preflight
   ↓
dati coerenti?
  /      \
 sì       no
 ↓         ↓
upgrade   ABORT
```

---

# 5. Integrità prodotto–immagine–documento

Per i documenti derivati da immagine viene consolidata una sola catena di identità:

```text
product_label_document
        ↓
product_image
        ↓
product
```

Per:

```text
source_type = 'image_derived'
```

il modello previsto è:

```text
product_image_id IS NOT NULL
product_id IS NULL
```

In questo modo il prodotto non viene registrato due volte nello stesso documento.

Il `product_id` diretto resta disponibile per sorgenti che non derivano da immagine, come eventuali:

```text
manual_input
structured_import
```

Questo evita il rischio di avere:

```text
document.product_id = prodotto A
document.product_image_id → prodotto B
```

---

# 6. Consolidamento del mapping degli ingredienti

Un candidato di mapping proveniente dal testo dell'etichetta deve rappresentare un ingrediente canonico WYE.

Il percorso diventa:

```text
testo etichetta
      ↓
ingrediente WYE
      ↓
ingredient_substances
      ↓
sostanza scientifica/regolatoria
```

Il candidato non deve quindi effettuare direttamente il mapping verso una sostanza.

Il vincolo previsto è:

```text
ingredient_id IS NOT NULL
substance_id IS NULL
```

La colonna `substance_id` può essere mantenuta temporaneamente per compatibilità, ma il suo utilizzo diretto nei candidati viene impedito.

La relazione ingrediente–sostanza resta responsabilità di:

```text
ingredient_substances
```

---

# 7. Relazione canonica tra ingredienti prodotto e review

La Fase 2 conteneva due possibili direzioni concorrenti:

```text
ingredient_mapping_reviews.product_ingredient_id
product_ingredients.mapping_review_id
```

La Fase 2.1 consolida una sola relazione canonica:

```text
product_ingredients
       1
       ↓
       N
ingredient_mapping_reviews
```

Quindi la review appartiene a una specifica occorrenza ingrediente del prodotto.

Questo permette anche di mantenere più review nel tempo:

```text
product ingredient
     ├── review 1
     ├── review 2
     └── review 3
```

La relazione inversa ridondante viene eliminata.

La review può comunque conservare snapshot e provenance utili all'audit, ad esempio:

```text
raw_text
normalized_text
provenance
```

---

# 8. Review accettate

Una review con:

```text
review_status = 'accepted'
```

deve avere esattamente un candidato selezionato.

Sono quindi vietati entrambi i casi:

```text
accepted + 0 candidati selezionati
accepted + 2 o più candidati selezionati
```

Lo stato valido è:

```text
accepted
   ↓
esattamente 1 candidate.is_selected = TRUE
```

La migration introduce un controllo database differito, in modo che l'invariante venga verificata al commit della transazione.

---

# 9. Introduzione di `storage_objects`

La Fase 2.1 introduce il concetto separato di oggetto fisico nello storage:

```text
storage_objects
```

Separando:

```text
storage_objects
= identità del blob immutabile

product_images
= utilizzo del blob per un prodotto,
  tipo immagine e specifica versione
```

La struttura prevista comprende informazioni come:

```text
id
storage_provider
bucket
object_key
object_version
checksum_algorithm
checksum_value
mime_type
byte_size
created_at
```

`product_images` viene collegata tramite:

```text
storage_object_id
```

Questo consente intenzionalmente a più record `product_images` di riferirsi allo stesso oggetto fisico.

Esempio:

```text
storage_object #42
      ↑
      ├── product_image A
      └── product_image B
```

È quindi possibile deduplicare il blob senza confondere l'identità fisica del file con il suo utilizzo applicativo.

Gli URL firmati, token temporanei o credenziali non devono essere salvati come identità persistente dello storage.

Il precedente:

```text
storage_reference
```

può restare temporaneamente per compatibilità con dati legacy.

---

# 10. Versionamento e supersession delle immagini

La Fase 2.1 rafforza le regole tra:

```text
is_current
status
superseded_at
superseded_by_image_id
```

Il database deve impedire stati incoerenti.

Esempi vietati:

```text
status = superseded
is_current = TRUE
```

oppure:

```text
is_current = TRUE
superseded_at IS NOT NULL
```

oppure una immagine rifiutata ancora marcata come corrente.

Viene inoltre impedita la self-reference:

```text
A → A
```

---

## 10.1 Supersession nello stesso prodotto e tipo

Una immagine può essere sostituita soltanto da un'altra immagine appartenente:

- allo stesso prodotto;
- allo stesso `image_type`.

Sono quindi vietati casi come:

```text
prodotto A → immagine prodotto B
```

o:

```text
ingredients → nutrition
```

La migration utilizza vincoli database per proteggere questa relazione.

---

## 10.2 Cicli nella supersession

Non devono essere possibili cicli come:

```text
A → B
B → C
C → A
```

La migration include un controllo differito per rilevare cicli nella catena di supersession.

Il controllo può quindi considerare lo stato finale della transazione prima del commit.

---

## 10.3 Immagine corrente

Resta il principio:

```text
un solo record current
per prodotto
per image_type
```

Questa garanzia sarà fondamentale durante la futura Fase 3, quando due upload potrebbero tentare contemporaneamente di sostituire la stessa immagine.

---

# 11. Checksum delle release scientifiche

La Fase 2 aveva un checksum globalmente unico.

La Fase 2.1 cambia la semantica.

L'identità del checksum viene contestualizzata tramite:

```text
dataset_id
checksum_algorithm
checksum
```

In questo modo:

```text
Dataset A → SHA256 XYZ
Dataset B → SHA256 XYZ
```

può essere consentito.

Ma nello stesso dataset:

```text
Dataset A → SHA256 XYZ
Dataset A → SHA256 XYZ
```

deve essere considerato duplicato.

Viene inoltre introdotto:

```text
checksum_algorithm
```

Non deve essere assunto automaticamente che i checksum legacy siano SHA-256 se l'algoritmo non è noto.

---

# 12. Preflight e protezione dei dati esistenti

La migration verifica i dati esistenti prima di applicare vincoli che potrebbero renderli invalidi.

Tra i casi da controllare rientrano:

- documenti `image_derived` incoerenti;
- candidati di mapping con identità invalide;
- relazioni review/product ingredient divergenti;
- supersession non valide;
- checksum incompatibili;
- riferimenti storage legacy non convertibili deterministicamente.

Principio fondamentale:

```text
dato ambiguo
≠
dato da correggere automaticamente
```

Se non esiste una trasformazione deterministica e sicura, la migration deve interrompersi.

---

# 13. Downgrade protetto

La migration include anche protezioni per il downgrade.

Il ritorno:

```text
0003 → 0002
```

non deve produrre perdita silenziosa di informazioni o ricostruire dati inventati.

Se lo stato del database utilizza funzionalità o relazioni introdotte dalla Fase 2.1 che non possono essere riportate in sicurezza allo schema precedente, il downgrade deve essere bloccato.

---

# 14. Test introdotti

È stato creato:

```text
backend/tests/test_data_integrity_hardening.py
```

La suite è progettata per verificare le nuove invarianti, tra cui:

- documenti image-derived;
- mapping candidati;
- review accettate;
- supersession delle immagini;
- cicli;
- storage objects;
- checksum;
- upgrade/downgrade;
- protezione da dati ambigui;
- concorrenza sull'immagine corrente.

Al momento, però, i test PostgreSQL d'integrazione non sono stati eseguiti perché manca un database di test esplicitamente autorizzato.

---

# 15. Verifiche effettivamente eseguite

Sono state eseguite con successo:

### Compilazione Python

La migration:

```text
0003_data_integrity_hardening.py
```

compila correttamente.

### Generazione SQL Alembic offline

La generazione SQL Alembic tramite:

```text
backend\venv
```

è riuscita.

Questo conferma che Alembic riesce a interpretare la migration e generare SQL.

Non equivale però alla sua esecuzione reale su PostgreSQL.

### Suite unittest

Risultato riportato:

```text
22 test
10 skip
2 errori
```

I test PostgreSQL che richiedono un database isolato sono stati saltati.

---

# 16. Problema preesistente OpenAI / httpx

I due errori riportati non derivano dalla Fase 2.1.

Sono relativi a:

```text
test_ai_normalizer
```

e all'incompatibilità tra le versioni installate di OpenAI e HTTPX.

Errore:

```text
Client.__init__() got an unexpected keyword argument 'proxies'
```

Questo problema era già esterno al perimetro della migration.

Dovrà essere risolto prima della futura fase OCR/AI, ma non dovrebbe essere mescolato con il lavoro di integrità del database.

---

# 17. Perché i test PostgreSQL non sono stati eseguiti

Il runner ha impedito correttamente alla migration di utilizzare il database predefinito.

Non è presente:

```text
WYE_TEST_DATABASE
```

che identifica esplicitamente un database sacrificabile e isolato destinato ai test.

Per eseguire la validazione completa è necessario configurare un database di test dedicato.

Esempio PowerShell:

```powershell
$env:WYE_TEST_DATABASE = "1"
$env:PGDATABASE = "wye_test"
```

Il database `wye_test` deve naturalmente esistere ed essere realmente dedicato ai test.

Non bisogna impostare `WYE_TEST_DATABASE=1` puntando al database di sviluppo o, soprattutto, di produzione.

---

# 18. Stato reale della Fase 2.1

Lo stato corretto è quindi:

```text
Codice migration              ✅ IMPLEMENTATO
Test dedicati                 ✅ IMPLEMENTATI
Compilazione Python           ✅ OK
SQL Alembic offline           ✅ OK

Upgrade PostgreSQL reale      ⏳ DA VERIFICARE
Downgrade PostgreSQL reale    ⏳ DA VERIFICARE
Constraint PostgreSQL         ⏳ DA VERIFICARE
Trigger differiti             ⏳ DA VERIFICARE
Test integrazione PostgreSQL  ⏳ DA ESEGUIRE
Test concorrenza              ⏳ DA ESEGUIRE

Suite generale                ⚠️ 2 errori preesistenti OpenAI/httpx
```

Per questo motivo la Fase 2.1 deve essere considerata:

```text
IMPLEMENTATA
ma
NON ANCORA VALIDATA COMPLETAMENTE
```

---

# 19. Criterio per considerare conclusa la Fase 2.1

La fase potrà essere marcata come completamente conclusa quando saranno eseguiti con successo almeno:

```text
0001 → 0002 → 0003
```

su PostgreSQL reale di test,

e:

```text
0003 → 0002
```

per il downgrade.

Dovranno inoltre passare i test PostgreSQL relativi a:

- documenti;
- mapping;
- review accepted;
- storage objects;
- supersession;
- cicli;
- checksum;
- concorrenza;
- preflight;
- downgrade protetto.

Gli errori `test_ai_normalizer` dovranno essere classificati separatamente perché preesistenti e non appartenenti alla Fase 2.1.

---

# 20. Prossimo passo immediato

Prima di iniziare la Fase 3 conviene completare una breve **Fase 2.1 Validation**:

```text
creare/configurare wye_test
        ↓
impostare WYE_TEST_DATABASE
        ↓
upgrade fino a 0003
        ↓
eseguire test PostgreSQL
        ↓
test concorrenza
        ↓
downgrade 0003 → 0002
        ↓
nuovo upgrade 0002 → 0003
        ↓
validazione finale
```

Solo dopo questo controllo sarà opportuno costruire la pipeline applicativa sopra il nuovo schema.

---

# 21. Fase successiva prevista

Una volta validata completamente la Fase 2.1, il progetto può passare alla:

# Fase 3 — Object Storage e acquisizione immagini

La Fase 3 utilizzerà le fondamenta appena consolidate per implementare:

```text
client
  ↓
richiesta upload
  ↓
object storage
  ↓
verifica/finalizzazione
  ↓
storage_objects
  ↓
product_images
  ↓
product_label_documents
```

La Fase 3 dovrà comprendere:

- scelta/configurazione del provider object storage;
- adapter storage;
- upload tramite URL firmati;
- validazione MIME e dimensione;
- checksum;
- finalizzazione idempotente;
- transazione di supersession;
- gestione concorrenza;
- gestione upload orfani;
- autorizzazione;
- accesso controllato alle immagini;
- creazione dei documenti etichetta.

Continueranno a restare fuori:

```text
OCR
AI
EFSA/OpenFoodTox
scoring
```

---

# 22. Roadmap aggiornata

```text
Fase 1
Alembic e baseline schema
✅ COMPLETATA

Fase 2
Modello dati scientifico e provenance
✅ COMPLETATA

Fase 2.1
Data Integrity Hardening
🟡 IMPLEMENTATA — VALIDAZIONE POSTGRESQL DA COMPLETARE

Fase 3
Object storage e acquisizione immagini
⏳ PROSSIMA DOPO VALIDAZIONE 2.1

Fase 4
OCR / AI / parsing etichetta
⏳ PIANIFICATA

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

# 23. Sintesi

La Fase 2.1 rende il database molto più rigoroso prima dell'introduzione delle pipeline applicative.

Le principali garanzie introdotte sono:

```text
documento image-derived
→ prodotto derivato dall'immagine

mapping etichetta
→ solo ingrediente WYE

ingrediente prodotto
→ più review storiche

review accepted
→ esattamente un candidato

storage object
→ separato dall'uso in product_images

supersession
→ stesso prodotto e stesso tipo

supersession
→ niente self-reference o cicli

release scientifiche
→ checksum contestuale al dataset

migration
→ abort sui dati ambigui
```

Il codice è stato creato e le verifiche statiche sono riuscite.

La priorità immediata non è aggiungere nuove funzionalità, ma eseguire la migration e i test su un **database PostgreSQL di test esplicitamente isolato**.

Solo dopo questa validazione la Fase 2.1 potrà essere considerata definitivamente conclusa e WYE potrà procedere in sicurezza alla Fase 3.
