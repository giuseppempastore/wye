# WYE — Riepilogo Fase 2 e piano della fase successiva

## 1. Stato del progetto

La **Fase 2 è stata implementata** con la migration Alembic:

```text
0002_scientific_data_model
```

Questa fase evolve il database di WYE per supportare in modo strutturato:

- immagini del prodotto conservate in object storage;
- provenienza e versionamento delle estrazioni da etichetta;
- normalizzazione controllata degli ingredienti;
- distinzione tra ingredienti WYE e sostanze scientifiche/regolatorie;
- dataset scientifici e relative release;
- assessment scientifici e finding;
- gestione esplicita dei mapping incerti o ambigui.

La Fase 2 riguarda esclusivamente il **modello dati**. Non introduce ancora pipeline applicative per upload, OCR, AI, import EFSA o scoring.

> Verifica diretta: il documento è stato aggiornato dopo l'ispezione della branch pubblica GitHub `ingredients_score`, al commit `d59bcac95e893c07f6a58328b77431a9b4ca413d` (`WYE - Codex Fase 2`). Sono stati esaminati direttamente la migration `0002_scientific_data_model.py`, il nuovo test `test_scientific_data_model.py` e il diff del commit.

---

## 2. Obiettivo architetturale raggiunto

La migration crea le fondamenta per il flusso futuro:

```text
immagine originale
→ documento etichetta
→ run OCR/AI versionata
→ item estratti
→ mapping controllato su ingrediente canonico
→ mapping ingrediente–sostanza
→ assessment scientifico versionato
→ scoring deterministico futuro
```

Il principio centrale resta:

```text
immagini originali = evidenza primaria
PostgreSQL = metadati, relazioni, provenienza e stato
object storage = contenuto binario delle immagini
```

Le immagini non vengono quindi salvate in PostgreSQL come `BYTEA`.

---

## 3. File introdotti nella Fase 2

Il commit verificato crea esclusivamente:

```text
backend/migrations/versions/0002_scientific_data_model.py
backend/tests/test_scientific_data_model.py
```

Non sono stati modificati:

- `README.md`;
- frontend;
- OCR;
- AI;
- upload immagini;
- ingestion EFSA;
- scoring;
- `postgres/01_wye_schema.sql`.

Il diff del commit conferma **504 righe aggiunte in due file**, senza altre modifiche. La mancata modifica di `postgres/01_wye_schema.sql` è coerente con la decisione presa nella Fase 1: da questo momento l'evoluzione dello schema viene gestita tramite Alembic. Resta comunque opportuno documentare esplicitamente quale procedura debba essere considerata canonica per creare un database nuovo.

---

## 4. Modifiche al modello dati

### 4.1 Immagini e provenienza object storage

È stata introdotta `product_images`, destinata a registrare i riferimenti alle immagini conservate fuori dal database.

Il modello implementa:

- relazione con il prodotto;
- tipo di immagine, per esempio fronte prodotto, ingredienti o tabella nutrizionale;
- riferimento all'oggetto nello storage;
- metadati tecnici;
- checksum;
- provenienza;
- stato e versionamento;
- individuazione dell'immagine corrente per ciascun tipo.

È stato aggiunto un vincolo che consente **una sola immagine corrente per prodotto e tipo**, mantenendo comunque le versioni precedenti.

Questo evita sovrascritture distruttive e permette di rieseguire in futuro OCR o analisi con modelli diversi.

### 4.2 Documenti di etichetta

È stata introdotta `product_label_documents`.

Un documento con `source_type = 'image_derived'` deve avere un `product_image_id`. Il vincolo protegge il primo livello della catena di provenienza:

```text
prodotto
→ immagine originale
→ documento etichetta
```

Il testo estratto non deve diventare una fonte indipendente priva del riferimento all'evidenza originale. La migration attuale, tuttavia, non garantisce che il `product_id` del documento coincida con quello dell'immagine collegata; questo punto deve essere corretto o fatto rispettare in modo transazionale dal servizio applicativo, preferibilmente con una garanzia anche a livello DB.

### 4.3 Run di estrazione

È stata introdotta `label_extraction_runs` per registrare ogni elaborazione OCR, parser o modello multimodale.

Lo scopo è conservare informazioni quali:

- metodo di estrazione;
- provider;
- modello e versione;
- versione del prompt o della procedura;
- risposta grezza;
- stato del run;
- data di esecuzione.

La stessa immagine potrà quindi essere rielaborata senza cancellare i risultati precedenti.

### 4.4 Item estratti

È stata introdotta `label_extraction_items` per separare le diverse informazioni individuate nell'etichetta, ad esempio:

- ingredienti;
- lista ingredienti;
- allergeni;
- valori nutrizionali;
- quantità;
- unità;
- altri elementi.

Questa separazione è necessaria per evitare che testo nutrizionale, allergeni e ingredienti vengano mescolati durante l'estrazione.

### 4.5 Sostanze scientifiche e identificatori

Sono state introdotte:

```text
substances
substance_identifiers
ingredient_substances
```

Il modello rende esplicita la distinzione:

```text
ingrediente canonico WYE ≠ necessariamente sostanza regolatoria
```

`substance_identifiers` permette di associare identificatori come E-number, CAS, EC, FL number o altri codici ufficiali.

`ingredient_substances` realizza una relazione molti-a-molti tra ingredienti e sostanze. Questo è essenziale perché:

- un ingrediente può corrispondere a più sostanze;
- una sostanza può comparire in più ingredienti o forme commerciali;
- il mapping può richiedere provenienza e governance proprie.

### 4.6 Dataset e release scientifiche

Sono state introdotte:

```text
source_datasets
source_dataset_releases
```

Il modello distingue ora l'organizzazione o fonte generale dal dataset concreto e dalla sua specifica release.

Esempio:

```text
EFSA
→ OpenFoodTox
→ release/versione acquisita da WYE
```

Questo permette di conservare versione, data, URL, checksum, formato, licenza e stato dell'importazione, rendendo le future ingestion riproducibili.

### 4.7 Assessment scientifici e finding

Sono state introdotte:

```text
scientific_assessments
scientific_assessment_findings
```

Il modello consente di collegare:

```text
sostanza
→ release del dataset
→ assessment
→ finding strutturati
```

Gli assessment possono conservare conclusioni e riferimenti documentali; i finding possono rappresentare endpoint, valori, unità, popolazione, contesto e tipo di evidenza.

Queste tabelle memorizzano evidenze scientifiche, ma **non assegnano automaticamente uno score WYE**.

### 4.8 Review dei mapping ingrediente

Sono state introdotte:

```text
ingredient_mapping_reviews
ingredient_mapping_review_candidates
```

Esse permettono di gestire un termine estratto non risolto in modo sicuro e auditabile, conservando candidati, metodo, confidence, motivazione, stato della review e selezione finale.

I vincoli implementati e testati richiedono:

- almeno un'identità valida per ogni candidato;
- al massimo un candidato selezionato per review.

Il `CHECK` usa attualmente una condizione `OR`: un candidato può quindi valorizzare contemporaneamente `ingredient_id` e `substance_id`. Se il dominio prevede una sola identità per candidato, il vincolo dovrebbe essere esclusivo, cioè un vero XOR.

Un candidato suggerito non diventa automaticamente un alias approvato.

### 4.9 Estensione di `ingredient_aliases`

`ingredient_aliases` è stata estesa in modo additivo per supportare alias multilingua e relativa governance.

Il comportamento desiderato resta:

```text
alias noto e approvato
→ mapping deterministico

alias sconosciuto o ambiguo
→ proposta di candidati
→ review
→ eventuale approvazione
```

La pipeline non deve creare automaticamente alias affidabili a partire da una sola risposta AI.

### 4.10 Estensione di `product_ingredients`

`product_ingredients` è stata estesa per conservare il legame con l'item estratto, il testo normalizzato, la lingua, il metodo di mapping, la confidence, lo stato e la provenienza.

La modifica più importante è:

```text
product_ingredients.ingredient_id = nullable
```

Un termine non risolto può quindi restare in uno degli stati:

```text
needs_review
ambiguous
unmapped
```

senza creare automaticamente:

- un ingrediente canonico;
- un alias approvato;
- una valutazione scientifica;
- un rischio arbitrario.

Questa scelta implementa il principio secondo cui **incertezza di mapping non significa rischio**.

---

## 5. Compatibilità e comportamento delle migration

### Upgrade da database vuoto

È stato eseguito:

```bash
python -m alembic -c backend/alembic.ini upgrade head
```

Risultato dichiarato:

```text
upgrade 0001 → 0002 riuscito
```

### Adozione di database legacy

È stato verificato il percorso:

```text
schema storico
→ stamp 0001
→ upgrade 0002
```

Il record prodotto preesistente è stato preservato:

```text
preserved_products = 1
revisione finale = 0002_scientific_data_model
```

### Downgrade

È stato eseguito il downgrade:

```bash
python -m alembic -c backend/alembic.ini downgrade 0001_initial_schema
```

Su un database senza dati della Fase 2 il downgrade è riuscito:

```text
product_images_after_downgrade = None
product_ingredients.ingredient_id torna NOT NULL
```

La migration contiene una protezione esplicita: il downgrade viene interrotto con un'eccezione se esiste almeno un `product_ingredients` con `ingredient_id = NULL`. Questo evita di forzare il ritorno a `NOT NULL` perdendo o falsificando mapping non risolti. Prima del downgrade in un ambiente reale tali record devono quindi essere risolti o gestiti tramite una procedura approvata.

---

## 6. Test e verifiche eseguite

Comandi riportati:

```bash
python -m alembic -c backend/alembic.ini upgrade head
python backend/scripts/baseline_existing_db.py
python -m alembic -c backend/alembic.ini downgrade 0001_initial_schema
python -m unittest discover -s backend/tests -v
```

Risultati:

```text
15/15 test OK
```

La suite comprende:

- 12 test preesistenti;
- 3 nuovi test d'integrazione.

I nuovi test coprono:

1. riferimento object storage e unicità dell'immagine corrente per tipo;
2. obbligo di collegare un documento derivato da immagine alla sua immagine originale;
3. identità obbligatoria dei candidati di mapping e unicità del candidato selezionato.

I database temporanei utilizzati per le verifiche risultano rimossi secondo il report di esecuzione. L'ispezione della repository conferma il codice dei tre test, ma non costituisce una riesecuzione indipendente dei test PostgreSQL: essi richiedono `WYE_TEST_DATABASE` e vengono altrimenti saltati tramite `@unittest.skipUnless`.

---

## 7. Decisioni confermate

La Fase 2 conferma i seguenti principi:

1. **PostgreSQL è la source of truth strutturata**, mentre le immagini risiedono in object storage.
2. **L'immagine originale è l'evidenza primaria** da cui derivano i documenti e le estrazioni.
3. **Ogni estrazione è versionata e tracciabile**; i risultati precedenti non devono essere sovrascritti.
4. **L'AI può proporre, non approvare autonomamente** ingredienti, alias o mapping scientifici.
5. **Ingrediente e sostanza regolatoria sono entità distinte**.
6. **Le fonti scientifiche devono essere versionate per dataset e release**.
7. **Gli assessment non sono lo score**: lo scoring sarà un livello successivo, deterministico e versionato.
8. **Un mapping sconosciuto rimane sconosciuto** e non riceve un rischio inventato.
9. La migration è stata mantenuta nel perimetro additivo richiesto, senza introdurre funzionalità applicative premature.

---

## 8. Elementi volutamente non implementati

Restano fuori dalla Fase 2:

- configurazione concreta dell'object storage;
- endpoint e servizio di upload;
- generazione di URL firmati;
- OCR o analisi multimodale;
- parser strutturato dell'etichetta;
- logica applicativa di mapping ingredienti;
- interfaccia di review;
- import EFSA/OpenFoodTox;
- scoring;
- storico degli score;
- job periodici;
- modifiche al frontend;
- correzioni manuali tramite `product_data_overrides`;
- eliminazione del catalogo scientifico/rischio hard-coded in Python.

---

## 9. Problema tecnico preesistente

Con chiavi AI configurate nell'ambiente, il backend entra nel percorso OpenAI e usa:

```python
client.responses
```

Il percorso risulta incompatibile con la dipendenza dichiarata:

```text
openai == 1.40.3
```

I test della Fase 2 sono stati eseguiti senza chiavi AI, usando il fallback locale previsto.

Il problema non è stato corretto perché era fuori dal perimetro della migration, ma deve essere risolto prima di implementare o testare seriamente la pipeline AI. Le alternative da valutare sono:

- aggiornare la libreria OpenAI a una versione che supporti l'API usata dal codice;
- adattare il codice all'interfaccia disponibile nella versione attualmente bloccata;
- aggiungere test separati per percorso AI e fallback locale.

La scelta va effettuata verificando compatibilità del progetto, changelog e comportamento del client, senza limitarsi ad aggiornare la dipendenza alla cieca.

---

## 10. Rischi e verifiche ancora consigliate

La revisione diretta della migration ha evidenziato i seguenti punti da risolvere o decidere prima della pipeline applicativa:

### 10.1 Integrità prodotto–immagine–documento

`product_label_documents` possiede sia `product_id` sia `product_image_id`, ma non esiste un vincolo che imponga che l'immagine appartenga allo stesso prodotto. È quindi tecnicamente possibile collegare il documento del prodotto A a un'immagine del prodotto B. Inoltre, per un documento `image_derived`, `product_id` può essere `NULL` anche quando l'immagine identifica già un prodotto.

Possibili soluzioni:

- eliminare la duplicazione e derivare sempre il prodotto dall'immagine;
- usare una foreign key composta che garantisca la corrispondenza;
- imporre la coerenza tramite trigger, mantenendo anche controlli applicativi.

### 10.2 Identità dei candidati di mapping

Il vincolo attuale richiede `ingredient_id IS NOT NULL OR substance_id IS NOT NULL`, quindi permette entrambi i campi valorizzati. Va deciso se ciò sia intenzionale. Se ogni candidato deve rappresentare esattamente un ingrediente oppure una sostanza, occorre un vincolo XOR.

### 10.3 Stato corrente e supersession delle immagini

L'indice parziale impedisce due immagini correnti con stato `pending_review`, `active` o `verified` per lo stesso prodotto e tipo. Non garantisce però da solo:

- coerenza tra `is_current`, `status`, `superseded_at` e `superseded_by_image_id`;
- appartenenza della nuova immagine allo stesso prodotto e tipo;
- assenza di cicli nella catena di supersession;
- aggiornamento atomico della vecchia e della nuova immagine.

Queste invarianti devono essere definite e testate nella Fase 3.

### 10.4 Unicità dei riferimenti storage

`storage_reference` è obbligatorio ma non univoco. Va stabilito se due record possano intenzionalmente riferirsi allo stesso oggetto. Se non è consentito, occorre un vincolo di unicità o una chiave strutturata con bucket/provider.

### 10.5 Unicità checksum delle release

`source_dataset_releases.checksum` è univoco globalmente quando valorizzato. Ciò impedisce che due record release, anche appartenenti a dataset diversi, registrino lo stesso identico artefatto. Può essere una scelta valida di deduplicazione, ma deve essere intenzionale; in alternativa l'unicità potrebbe essere contestuale al dataset o al relativo algoritmo di checksum.

### 10.6 Relazione circolare review–occorrenza

`ingredient_mapping_reviews.product_ingredient_id` punta a `product_ingredients`, mentre `product_ingredients.mapping_review_id` punta nuovamente a `ingredient_mapping_reviews`. La relazione è gestibile perché entrambe le foreign key sono nullable, ma crea due possibili fonti di verità. Occorre stabilire quale collegamento sia canonico e impedire coppie incoerenti.

### 10.7 Copertura dei test

I tre test aggiunti confermano i vincoli dichiarati, ma non coprono ancora diversi casi critici. In particolare, il test sul documento verifica soltanto che un documento derivato non possa essere privo di immagine; non verifica la corrispondenza del prodotto. Il test sui candidati verifica “almeno una identità”, non “esattamente una”.

Restano inoltre da verificare:

- adeguatezza delle azioni `ON DELETE` rispetto ai flussi applicativi futuri;
- sufficienza degli indici rispetto alle query reali della pipeline;
- vincoli parziali sull'unicità delle immagini correnti e dei candidati selezionati;
- gestione dei checksum e delle chiavi object storage;
- vincoli tra `product_id`, immagine e documento per evitare collegamenti incrociati;
- immutabilità o append-only dei record di provenienza;
- stati consentiti e transizioni applicative;
- timezone dei timestamp;
- procedura operativa di downgrade quando esistono record con `ingredient_id = NULL`;
- compatibilità reale con un dump rappresentativo del database di produzione;
- assenza di divergenza involontaria tra Alembic e `postgres/01_wye_schema.sql`.

È inoltre consigliabile aggiungere test per:

- sostituzione/versionamento di un'immagine corrente;
- impossibilità di collegare un documento a un'immagine di un altro prodotto;
- unicità e namespace degli identificatori di sostanza;
- duplicazione delle release di dataset;
- integrità della relazione assessment–release–sostanza;
- mapping accettato, rifiutato, ambiguo e non risolto;
- downgrade con dati Fase 2 presenti;
- concorrenza nella selezione del candidato o dell'immagine corrente.

---

# 11. Fase successiva proposta: acquisizione immagini e documenti etichetta

La fase successiva consigliata è una **Fase 3 limitata alla pipeline di acquisizione**, senza introdurre ancora AI, EFSA o scoring.

L'obiettivo è rendere utilizzabile il primo tratto del modello appena creato:

```text
client
→ richiesta upload
→ object storage
→ conferma upload
→ product_images
→ creazione documento etichetta
```

Questa separazione consente di testare sicurezza, integrità e provenienza prima di aggiungere l'incertezza di OCR e modelli multimodali.

## 11.1 Decisioni da prendere prima dell'implementazione

### Provider object storage

Scegliere il provider iniziale, per esempio:

- Amazon S3;
- Cloudflare R2;
- Supabase Storage;
- MinIO per sviluppo locale;
- altro servizio compatibile S3.

È preferibile isolare il provider dietro un'interfaccia applicativa, evitando che endpoint e dominio dipendano direttamente da uno specifico SDK.

### Modello di upload

Approccio consigliato:

```text
1. il backend autorizza l'upload;
2. genera una chiave storage non prevedibile e un URL firmato;
3. il client carica direttamente l'immagine;
4. il backend verifica e finalizza il record;
5. l'immagine diventa disponibile per le elaborazioni successive.
```

Il backend non dovrebbe fidarsi dei soli metadati dichiarati dal client.

### Policy di conservazione

Definire:

- dimensione massima;
- MIME type ammessi;
- estensioni accettate;
- checksum richiesto;
- gestione EXIF e metadati sensibili;
- lifecycle degli upload incompleti;
- retention delle versioni sostituite;
- cancellazione logica e fisica;
- cifratura;
- autorizzazioni di lettura;
- eventuale scansione malware.

## 11.2 Implementazione backend proposta

La Fase 3 dovrebbe includere:

1. configurazione object storage tramite variabili d'ambiente;
2. adapter/service per lo storage;
3. endpoint per inizializzare un upload;
4. endpoint per finalizzarlo dopo verifica;
5. persistenza in `product_images`;
6. servizio per rendere corrente una nuova immagine e supersedere quella precedente in transazione;
7. endpoint per elencare le immagini di un prodotto;
8. URL di lettura firmati o accesso mediato;
9. creazione controllata di `product_label_documents` a partire da immagini ammissibili;
10. logging e gestione degli errori senza esporre credenziali o chiavi storage.

## 11.3 Test minimi della Fase 3

La suite dovrebbe coprire almeno:

- upload valido;
- MIME type non ammesso;
- file troppo grande;
- checksum errato;
- finalizzazione senza oggetto presente;
- doppia finalizzazione idempotente;
- accesso a un prodotto non autorizzato;
- nuova immagine che supersede correttamente la precedente;
- concorrenza tra due upload dello stesso tipo;
- rollback DB se la finalizzazione fallisce;
- pulizia degli upload incompleti;
- impossibilità di creare un documento da un'immagine incompatibile;
- impossibilità di collegare prodotto, immagine e documento appartenenti a entità diverse.

Per i test automatici è utile prevedere un adapter fake/in-memory e almeno un test d'integrazione con uno storage S3-compatible locale o dedicato ai test.

## 11.4 Criteri di completamento della Fase 3

La Fase 3 può considerarsi conclusa quando:

- un'immagine viene caricata senza transitare stabilmente nel database;
- il record contiene riferimento storage, checksum e provenienza verificabili;
- una nuova immagine dello stesso tipo sostituisce logicamente la precedente senza cancellarla;
- gli accessi sono autorizzati;
- gli upload incompleti e gli errori non lasciano record incoerenti;
- il documento etichetta conserva il legame con l'immagine originale;
- i test unitari e d'integrazione passano;
- non sono ancora stati introdotti OCR, AI, EFSA o scoring.

---

## 12. Fasi successive previste

Dopo la Fase 3, il percorso consigliato è:

### Fase 4 — OCR/estrazione e provenienza

- creare `product_label_documents` dal contenuto delle immagini;
- registrare `label_extraction_runs`;
- produrre `label_extraction_items` strutturati;
- distinguere ingredienti, allergeni, nutrizione, quantità e unità;
- risolvere l'incompatibilità del client OpenAI;
- aggiungere test con risposte registrate/fake e test d'integrazione separati.

### Fase 5 — Normalizzazione e review dei mapping

- lookup deterministico degli alias approvati;
- generazione controllata dei candidati;
- stati `accepted`, `needs_review`, `ambiguous`, `unmapped`, `rejected`;
- interfaccia o API di review;
- promozione esplicita di un mapping validato ad alias riutilizzabile;
- nessuna creazione autonoma di ingredienti canonici da parte dell'AI.

### Fase 6 — Ingestion EFSA/OpenFoodTox

- download e identificazione delle release;
- checksum e provenance;
- import idempotente;
- mapping sugli identificatori di sostanza;
- assessment e finding strutturati;
- changelog e identificazione delle sostanze interessate da una nuova release.

### Fase 7 — Scoring scientifico versionato

- definizione formale del modello di scoring;
- separazione tra `Safety Score` ed `Evidence Confidence`;
- risultato nullo in caso di evidenza insufficiente;
- versione del modello;
- input e output riproducibili;
- storico degli score;
- ricalcolo dei soli ingredienti interessati da variazioni delle fonti.

---

## 13. Prompt operativo consigliato per Codex — Fase 3

Usare come base la branch pubblica [`ingredients_score`](https://github.com/giuseppempastore/wye/tree/ingredients_score) e chiedere a Codex di partire dal commit della Fase 2 o da un suo discendente verificato.

```text
La Fase 2 del progetto WYE è conclusa con la migration
`0002_scientific_data_model`.

Procedi prima con una revisione read-only della repository aggiornata e verifica:

- schema reale introdotto dalla migration 0002;
- vincoli e indici di product_images e product_label_documents;
- struttura FastAPI e pattern di accesso PostgreSQL esistenti;
- autenticazione/autorizzazione disponibile;
- configurazione e test correnti;
- problema di compatibilità tra `client.responses` e `openai==1.40.3`.

Poi proponi un piano dettagliato per la Fase 3, limitata a:

- integrazione object storage;
- upload sicuro delle immagini;
- persistenza e versionamento in product_images;
- creazione controllata di product_label_documents;
- test unitari e d'integrazione.

Vincoli:

- nessun BYTEA;
- nessun OCR o AI in questa fase;
- nessuna ingestion EFSA;
- nessuno scoring;
- nessuna modifica distruttiva;
- nessun refactoring non necessario;
- non modificare il frontend finché il contratto API non è approvato;
- non implementare prima di aver mostrato il piano, le decisioni aperte e i file previsti.

Nel piano includi:

1. provider e adapter storage consigliato;
2. flusso upload/finalizzazione;
3. endpoint e payload;
4. autorizzazione;
5. validazione MIME, dimensione e checksum;
6. transazione per is_current/supersession;
7. idempotenza e concorrenza;
8. gestione upload orfani;
9. test previsti;
10. variabili d'ambiente e documentazione da aggiornare.

Non scrivere codice finché il piano non viene approvato.
```

---

## 14. Stato finale sintetico

```text
Fase 1 — Alembic e baseline schema                 COMPLETATA
Fase 2 — Modello dati scientifico e provenance     COMPLETATA
Fase 3 — Object storage e acquisizione immagini    PROSSIMA
Fase 4 — OCR/AI e parsing etichetta                 PIANIFICATA
Fase 5 — Mapping e review                           PIANIFICATA
Fase 6 — EFSA/OpenFoodTox ingestion                 PIANIFICATA
Fase 7 — Scoring scientifico versionato             PIANIFICATA
```

La Fase 2 ha costruito il livello dati necessario per evitare scorciatoie pericolose: nessuna immagine nel database, nessun mapping inventato, nessun ingrediente creato automaticamente e nessuno score derivato direttamente da una risposta AI. Il prossimo passo corretto è rendere affidabile la catena di acquisizione dell'evidenza primaria prima di aggiungere OCR e interpretazione automatica.
