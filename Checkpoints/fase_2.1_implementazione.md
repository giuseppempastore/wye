# WYE — Fase 2.1: Data Integrity Hardening

## Stato

**COMPLETATA E VALIDATA**

Branch:

```text
ingredients_score
```

Commit di partenza:

```text
d59bcac — WYE - Codex Fase 2
```

La Fase 2.1 è stata implementata e validata realmente su PostgreSQL 18.6 usando esclusivamente il database isolato:

```text
wye_test
```

La Fase 3 non è ancora iniziata.

---

## 1. Obiettivo della fase

La Fase 2 aveva introdotto il modello dati scientifico e di provenance di WYE.

Prima di costruire upload, OCR, AI, ingestion EFSA e scoring, la Fase 2.1 ha rafforzato il database per impedire stati incoerenti.

Principio:

```text
prima rendere il modello dati robusto
→ poi costruire le pipeline applicative
```

---

## 2. File creati

```text
backend/migrations/versions/0003_data_integrity_hardening.py
backend/tests/test_data_integrity_hardening.py
```

Non è stata modificata:

```text
backend/migrations/versions/0002_scientific_data_model.py
```

Nessun file frontend, README o altro file applicativo è stato modificato.

---

## 3. Migration introdotta

```text
0003_data_integrity_hardening
```

La migration è stata verificata realmente attraverso:

```text
0001_initial_schema
→ 0002_scientific_data_model
→ 0003_data_integrity_hardening
```

Risultato:

```text
OK
```

È stato testato anche l'upgrade da un database già a `0002` contenente dati coerenti.

I dati esistenti sono stati preservati.

---

## 4. Preflight transazionale

Prima di applicare modifiche restrittive, la migration controlla che i dati esistenti siano compatibili.

Se trova una situazione ambigua o non correggibile deterministicamente:

```text
migration → ABORT
```

senza lasciare modifiche parziali nel database.

Sono stati verificati casi di abort per:

- documento image-derived associato al prodotto sbagliato;
- candidato mapping con ingrediente e sostanza contemporaneamente;
- review e product ingredient divergenti;
- supersession immagini invalida;
- checksum release ambiguo o vuoto.

---

## 5. Documenti derivati da immagine

Per:

```text
source_type = image_derived
```

il prodotto viene derivato dall'immagine:

```text
product_label_document
        ↓
product_image
        ↓
product
```

Il modello evita quindi di mantenere due identità concorrenti del prodotto.

Quando il `product_id` del documento era ridondante ma coerente con l'immagine, il backfill lo ha rimosso.

---

## 6. Mapping ingredienti

I candidati provenienti dal testo dell'etichetta possono rappresentare esclusivamente ingredienti canonici WYE.

Flusso:

```text
testo etichetta
      ↓
ingrediente WYE
      ↓
ingredient_substances
      ↓
sostanza scientifica/regolatoria
```

Il mapping diretto del testo verso una sostanza è impedito.

---

## 7. Review dei mapping

La relazione canonica è ora:

```text
product_ingredients
       1
       ↓
       N
ingredient_mapping_reviews
```

Un ingrediente presente in un prodotto può quindi avere più review nel tempo.

Le relazioni legacy coerenti sono state consolidate su:

```text
product_ingredient_id
```

---

## 8. Review accettata

Una review:

```text
review_status = accepted
```

deve avere esattamente un candidato selezionato.

Sono vietati:

```text
accepted + 0 candidati selezionati
accepted + più di 1 candidato selezionato
```

Il controllo viene eseguito tramite trigger differito al commit.

Durante la validazione sono stati individuati e corretti due bug nel trigger:

1. accesso non valido a `NEW.review_id` sugli eventi della tabella review;
2. mancata rivalidazione della review precedente quando un candidato veniva spostato.

---

## 9. Storage objects

È stata introdotta:

```text
storage_objects
```

Distinzione:

```text
storage_objects
= identità del blob fisico immutabile

product_images
= utilizzo/versione del blob per un prodotto
```

Più `product_images` possono intenzionalmente puntare allo stesso `storage_object`.

L'identità fisica dello storage è protetta da vincoli di unicità.

I riferimenti storage legacy non strutturati non vengono interpretati artificialmente:

```text
storage_reference = preservato
storage_object_id = NULL
```

Non vengono inventati:

- provider;
- bucket;
- object version;
- metadata non disponibili.

---

## 10. Versionamento immagini

Sono stati rafforzati i vincoli tra:

```text
is_current
status
superseded_at
superseded_by_image_id
```

Il database impedisce stati incoerenti.

È inoltre vietata la supersession:

- verso la stessa immagine;
- verso un altro prodotto;
- verso un altro image type.

---

## 11. Anti-ciclo

Catene come:

```text
A → B
B → C
C → A
```

sono impedite tramite trigger differito.

Una normale catena storica:

```text
A → B → C
```

resta valida.

---

## 12. Concorrenza

È stato eseguito un test PostgreSQL reale con due connessioni a isolamento:

```text
READ COMMITTED
```

Entrambe hanno tentato di sostituire contemporaneamente la stessa immagine corrente.

Risultato:

```text
transazione 1 → COMMIT
transazione 2 → UniqueViolation
```

Stato finale:

```text
una sola immagine current
```

L'invariante è protetta dall'indice:

```text
uq_product_images_current_type
```

---

## 13. Checksum release scientifiche

Il checksum non è più trattato come globalmente unico.

L'unicità è contestualizzata da:

```text
dataset_id
checksum_algorithm
checksum
```

Quindi lo stesso artefatto può essere legittimamente presente in dataset differenti.

Per i checksum legacy, l'algoritmo non viene inventato.

Quando non noto viene marcato esplicitamente:

```text
unknown
```

---

## 14. Downgrade

È stato verificato:

```text
0003 → 0002
```

su dati compatibili.

Risultato:

```text
OK
```

Sono stati rimossi correttamente:

- `storage_objects`;
- nuove colonne;
- constraint;
- foreign key;
- trigger;
- funzioni PostgreSQL;
- indici introdotti dalla `0003`.

Quando il downgrade provocherebbe perdita di informazioni, viene bloccato.

Esempio verificato:

```text
product_images collegata a storage_objects
→ downgrade BLOCCATO
```

senza modifiche parziali.

---

## 15. Re-upgrade

Dopo il downgrade è stato verificato nuovamente:

```text
0002 → 0003
```

Risultato:

```text
OK
```

Revisione finale:

```text
0003_data_integrity_hardening (head)
```

---

## 16. Risultati dei test

### Test database Fase 2 / 2.1

```text
Totale: 14
Passed: 14
Failed: 0
Errors: 0
Skipped: 0
```

Quindi:

```text
14 / 14 OK
```

### Suite backend completa

```text
Totale: 26
Passed: 24
Failed: 0
Errors: 2
Skipped: 0
```

I due errori residui sono preesistenti e fuori scope:

```text
Client.__init__() got an unexpected keyword argument 'proxies'
```

Riguardano:

```text
openai / httpx
test_ai_normalizer
```

e non la Fase 2.1.

---

## 17. Stato repository

Branch:

```text
ingredients_score
```

Commit iniziale:

```text
d59bcac — WYE - Codex Fase 2
```

Al termine della validazione Codex non ha creato un nuovo commit.

I due nuovi file risultano ancora non tracciati:

```text
backend/migrations/versions/0003_data_integrity_hardening.py
backend/tests/test_data_integrity_hardening.py
```

Questo significa che il prossimo passaggio operativo deve includere il loro inserimento nel versionamento Git.

---

## 18. Stato finale della Fase 2.1

```text
Migration 0003                    ✅
Preflight transazionale           ✅
Storage objects                   ✅
Integrità documenti               ✅
Mapping candidates                ✅
Review 1:N                        ✅
Review accepted                   ✅
Supersession immagini             ✅
Anti-cycle                        ✅
Checksum dataset                  ✅
Upgrade PostgreSQL                ✅
Downgrade PostgreSQL              ✅
Re-upgrade                        ✅
Concorrenza                       ✅
Test DB                           ✅ 14/14

Problema OpenAI/httpx              ⚠️ preesistente
Commit Git della Fase 2.1         ⏳ ancora da creare
```

La Fase 2.1 è quindi:

# ✅ COMPLETATA

Il mancato commit non cambia la validità tecnica della fase, ma va sistemato prima di continuare lo sviluppo.

---

## 19. Prossimo passo

Prima di iniziare la Fase 3:

```text
verificare git diff/status
→ aggiungere i due file
→ creare commit Fase 2.1
→ verificare worktree pulito
```

Dopodiché potrà iniziare:

# Fase 3 — Object Storage e acquisizione immagini

Obiettivo futuro:

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

La Fase 3 non dovrà ancora introdurre:

```text
OCR
AI
EFSA/OpenFoodTox
scoring
```

---

## 20. Roadmap

```text
Fase 1
Alembic e baseline schema
✅ COMPLETATA

Fase 2
Modello dati scientifico e provenance
✅ COMPLETATA

Fase 2.1
Data Integrity Hardening
✅ COMPLETATA

Fase 3
Object storage e acquisizione immagini
⏳ PROSSIMA

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
