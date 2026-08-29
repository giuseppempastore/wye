# WYE — Stato del progetto

Questo file serve come riepilogo semplice e leggibile dello stato attuale di WYE.

## Dove siamo

```text
Fase 1      ✅ COMPLETATA
Fase 2      ✅ COMPLETATA
Fase 2.1    ✅ COMPLETATA
Fase 3      ✅ COMPLETATA
Fase 3.1    ✅ COMPLETATA
Fase 4      ✅ COMPLETATA + E2E
Fase 5      ✅ COMPLETATA + E2E
Fase 6      ✅ COMPLETATA
Fase 7      ⏳ FUTURA — ARCHITETTURA/SCORING DA PROGETTARE
```

---

## Fase 1 — Fondamenta database

È stato introdotto Alembic per gestire in modo controllato l'evoluzione del database PostgreSQL.

In pratica:

```text
schema database
→ versionato
→ aggiornabile tramite migration
```

---

## Fase 2 — Modello scientifico e provenance

È stato costruito il modello dati necessario per rappresentare:

- immagini prodotto;
- documenti etichetta;
- estrazioni versionate;
- ingredienti;
- sostanze scientifiche;
- mapping;
- review;
- dataset scientifici;
- release;
- assessment.

L'obiettivo era preparare il database senza implementare ancora upload, OCR, AI o scoring.

---

## Fase 2.1 — Integrità del modello

È stata aggiunta la migration:

```text
0003_data_integrity_hardening
```

che impedisce molte incoerenze direttamente a livello PostgreSQL.

Tra le protezioni:

- prodotto derivato correttamente dall'immagine;
- mapping del testo solo verso ingredienti WYE;
- review storiche 1:N;
- una review accepted deve avere un solo candidato;
- separazione tra file storage e product image;
- versionamento immagini coerente;
- niente cicli nelle supersession;
- checksum scientifici contestualizzati al dataset;
- abort sicuro della migration sui dati ambigui.

La migration è stata validata realmente su PostgreSQL 18.6.

Test database:

```text
14 / 14 OK
```

Upgrade, downgrade e re-upgrade:

```text
OK
```

Test di concorrenza:

```text
OK
```

---

## Problema tecnico ancora aperto

La suite backend completa presenta ancora due errori preesistenti:

```text
Client.__init__() got an unexpected keyword argument 'proxies'
```

relativi alla compatibilità:

```text
openai ↔ httpx
```

Non appartengono alla Fase 2.1.

Questo problema dovrà essere risolto prima di lavorare seriamente sulla futura pipeline AI.

---

## Operazione Git ancora da fare

Codex ha creato ma non ancora committato:

```text
backend/migrations/versions/0003_data_integrity_hardening.py
backend/tests/test_data_integrity_hardening.py
```

Prima di iniziare la Fase 3 conviene creare un commit dedicato alla Fase 2.1.

---

# Prossima fase

## Fase 3 — Object Storage e acquisizione immagini

Sarà il primo vero pezzo applicativo che utilizza il modello appena costruito.

Flusso previsto:

```text
utente/client
    ↓
richiesta upload
    ↓
object storage
    ↓
verifica file
    ↓
storage_objects
    ↓
product_images
    ↓
product_label_documents
```

La fase dovrà affrontare:

- scelta/configurazione object storage;
- adapter backend;
- upload sicuro;
- URL firmati;
- MIME type;
- dimensione massima;
- checksum;
- finalizzazione;
- idempotenza;
- concorrenza;
- immagini obsolete/superseded;
- upload incompleti;
- autorizzazioni.

Non entreranno ancora:

```text
OCR
AI
EFSA/OpenFoodTox
scoring
```

---

# Visione complessiva

```text
IMMAGINE PRODOTTO
       ↓
[Fase 3]
Acquisizione sicura
       ↓
[Fase 4]
OCR / AI / parsing
       ↓
[Fase 5]
Normalizzazione + review
       ↓
[Fase 6]
Evidenza EFSA/OpenFoodTox
       ↓
[Fase 7]
Scoring scientifico versionato
```

Lo stato attuale del progetto può quindi essere riassunto così:

> Le Fasi 1–6 sono consolidate. WYE conserva evidenze scientifiche versionate e
> tracciabili da EFSA e OpenFoodTox, con identity resolution, provenance,
> batch/recovery e traversal prodotto → evidenza. La Fase 7 dovrà progettare lo
> scoring senza alterare il principio `scientific evidence != scientific scoring`.
