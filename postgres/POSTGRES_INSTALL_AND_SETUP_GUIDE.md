# Guida completa: installazione e setup di PostgreSQL per WYE

Questo documento spiega passo dopo passo come installare PostgreSQL in locale, verificare il servizio, creare il database `wye` e applicare lo schema SQL del progetto.

Obiettivo: capire esattamente cosa è stato fatto e come ripeterlo manualmente in un'altra sessione, senza dover reinventare i passaggi.

---

## 1. Premessa

Il progetto WYE usa PostgreSQL come database relazionale per memorizzare:
- prodotti
- ingredienti
- alias e mapping ingredienti
- allergeni
- nutrizione
- utenti premium
- score e logica di valutazione

Per questo abbiamo creato:
- il database `wye`
- lo schema SQL in `postgres/01_wye_schema.sql`
- la checklist di progresso in `postgres/WYE_DB_SETUP_PROGRESS.md`

---

## 2. Cosa ho verificato prima di creare il database

Ho controllato che PostgreSQL fosse installato e attivo sul PC.

### Comando eseguito

```powershell
$commands = Get-Command psql,pg_isready -ErrorAction SilentlyContinue
if ($commands) {
    $commands | Select-Object Name,Source,Version | Format-Table -AutoSize
} else {
    "PostgreSQL client not found"
}
Get-Service postgres* -ErrorAction SilentlyContinue | Select-Object Name,Status,DisplayName | Format-Table -AutoSize
```

### Risultato verificato
- `PostgreSQL client not found` nel PATH standard
- servizio attivo: `postgresql-x64-18`

Questo ha confermato che PostgreSQL era già installato e in esecuzione come servizio Windows.

---

## 3. Ho trovato il percorso del client `psql`

Poiché il client non era nel PATH, ho cercato il binario installato.

### Comando eseguito

```powershell
Get-ChildItem "C:\Program Files\PostgreSQL" -Recurse -Filter psql.exe -ErrorAction SilentlyContinue |
Select-Object -First 10 |
ForEach-Object { $_.FullName }
```

### Percorso trovato

```text
C:\Program Files\PostgreSQL\18\bin\psql.exe
```

Questo è importante perché i comandi PostgreSQL vanno spesso eseguiti usando un percorso assoluto quando il client non è disponibile nel PATH di sistema.

---

## 4. Ho verificato che il server risponde

Ho connesso il client `psql` al server locale con l'utente `postgres`.

### Comando eseguito

```powershell
$env:PGPASSWORD = 'negletto87'
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d postgres -c "SELECT current_user, current_database(), version();"
```

### Cosa fa
- usa la password di `postgres`
- si collega a `localhost`
- usa il database di default `postgres`
- esegue una query di test

### Risultato atteso

```text
 current_user | current_database | version
--------------+------------------+--------------------------------------
 postgres     | postgres         | PostgreSQL 18.6 on x86_64-windows ...
```

Se questo comando funziona, il server PostgreSQL è raggiungibile e puoi creare database e tabelle.

---

## 5. Ho creato il database WYE

Il database dedicato al progetto si chiama `wye`.

### Comando eseguito

```powershell
$env:PGPASSWORD = 'negletto87'
$psql = 'C:\Program Files\PostgreSQL\18\bin\psql.exe'
$dbExists = & $psql -U postgres -h localhost -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = 'wye';"
if ($dbExists -ne '1') {
    & $psql -U postgres -h localhost -d postgres -c "CREATE DATABASE wye;"
}
```

### Cosa fa
- controlla se `wye` esiste già
- se non esiste, lo crea

### Nota importante
Di solito è meglio non usare il database `postgres` per il progetto, ma dedicare un database specifico come `wye`.

---

## 6. Ho applicato lo schema SQL

Lo schema del database è contenuto in:

```text
postgres/01_wye_schema.sql
```

### Comando eseguito

```powershell
& $psql -U postgres -h localhost -d wye -f "C:\Projects\wye\postgres\01_wye_schema.sql"
```

Questo comando esegue tutte le istruzioni SQL del file, tra cui:
- `CREATE TABLE ...`
- `CREATE INDEX ...`
- definizione di PK/FK
- vincoli `CHECK`
- campi di tipo `TIMESTAMPTZ`

### A cosa serve lo schema
Lo script crea tutte le tabelle del progetto:
- `products`
- `ingredients`
- `ingredient_aliases`
- `ingredient_categories`
- `ingredient_risk_profiles`
- `allergens`
- `ingredient_allergens`
- `sources`
- `ingredient_evidence`
- `product_ingredients`
- `nutrition_facts`
- `nutrition_thresholds`
- `product_scores`
- `cosmetics_products`
- `cosmetic_ingredient_assessment`
- `users`
- `user_profiles`
- `user_allergies`
- `product_reviews`

---

## 7. Ho verificato che le tabelle fossero create

### Comando eseguito

```powershell
& $psql -U postgres -h localhost -d wye -c "\dt"
```

### Output verificato

```text
List of tables
 Schema | Name | Type | Owner
--------+----------------------------+-------+----------
 public | allergens | table | postgres
 public | cosmetic_ingredient_assessment | table | postgres
 public | cosmetics_products | table | postgres
 public | ingredient_aliases | table | postgres
 public | ingredient_allergens | table | postgres
 public | ingredient_categories | table | postgres
 public | ingredient_evidence | table | postgres
 public | ingredient_risk_profiles | table | postgres
 public | ingredients | table | postgres
 public | nutrition_facts | table | postgres
 public | nutrition_thresholds | table | postgres
 public | product_ingredients | table | postgres
 public | product_reviews | table | postgres
 public | product_scores | table | postgres
 public | products | table | postgres
 public | sources | table | postgres
 public | user_allergies | table | postgres
 public | user_profiles | table | postgres
 public | users | table | postgres
```

Questo conferma che lo schema è stato applicato correttamente.

---

## 8. Ho provato un inserimento di test

Per essere sicuro che il database non solo avesse le tabelle, ma anche funzionasse correttamente, ho fatto un inserimento di prova.

### Comando eseguito

```powershell
$env:PGPASSWORD = 'negletto87'
$psql = 'C:\Program Files\PostgreSQL\18\bin\psql.exe'
& $psql -U postgres -h localhost -d wye -c "INSERT INTO products (barcode, brand_name, product_name, category, product_type, source, verified, status) VALUES ('1234567890123', 'TestBrand', 'Test Product', 'food', 'snack', 'manual', TRUE, 'active') ON CONFLICT (barcode) DO NOTHING; SELECT id, barcode, product_name, category FROM products WHERE barcode = '1234567890123';"
```

### Risultato

```text
INSERT 0 1
 id | barcode | product_name | category
----+---------------+--------------+----------
 1 | 1234567890123 | Test Product | food
```

Questo dimostra che:
- le tabelle esistono
- la connessione è valida
- gli insert funzionano
- le query leggono correttamente i dati

---

## 9. Come ripeterlo manualmente in futuro

Se dovessi rifare tutto da zero, i passaggi essenziali sono questi:

### Passo 1: controllare se PostgreSQL è installato

```powershell
Get-Service postgres* -ErrorAction SilentlyContinue
```

### Passo 2: localizzare il client `psql`

```powershell
Get-ChildItem "C:\Program Files\PostgreSQL" -Recurse -Filter psql.exe -ErrorAction SilentlyContinue
```

### Passo 3: connettersi al server

```powershell
$env:PGPASSWORD = 'negletto87'
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d postgres -c "SELECT version();"
```

### Passo 4: creare il database

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d postgres -c "CREATE DATABASE wye;"
```

### Passo 5: eseguire lo schema

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d wye -f "C:\Projects\wye\postgres\01_wye_schema.sql"
```

### Passo 6: verificare le tabelle

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d wye -c "\dt"
```

### Passo 7: fare un test di inserimento

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d wye -c "INSERT INTO products (barcode, brand_name, product_name, category, product_type, source, verified, status) VALUES ('1234567890123', 'TestBrand', 'Test Product', 'food', 'snack', 'manual', TRUE, 'active');"
```

---

## 10. Se PostgreSQL non è ancora installato

Se dovesse mancare in futuro, la procedura standard su Windows è:

1. scaricare PostgreSQL da https://www.postgresql.org/download/windows/
2. avviare l'installer
3. scegliere la versione desiderata (nel nostro caso 18)
4. impostare la password per l'utente `postgres`
5. installare anche pgAdmin, se desiderato
6. lasciare il servizio attivo
7. verificare che il servizio si avvii correttamente

### Password usata nel progetto

Nel workspace è presente:

```text
postgres/user_postgres.txt
```

con i dati:

```text
username:
postgres

password:
negletto87
```

---

## 11. File importanti nel progetto

- `postgres/01_wye_schema.sql` -> schema del database
- `postgres/WYE_DB_SETUP_PROGRESS.md` -> checklist del progresso
- `postgres/user_postgres.txt` -> credenziali di accesso locale

---

## 12. Ripasso finale

Il processo fatto in pratica è stato:

1. controllare installazione PostgreSQL
2. verificare che il servizio sia attivo
3. individuare il client `psql`
4. collegarsi al server locale
5. creare il database `wye`
6. importare lo schema SQL
7. verificare le tabelle
8. testare un insert e una select

Questo è il minimo indispensabile per poter ricreare dal zero il database del progetto WYE.

---

## 13. Consiglio pratico

Anche se il database è già pronto, conviene conservare sempre:
- la password del superutente `postgres`
- il path del client `psql`
- il file SQL di schema versionato nel repo
- una checklist del progresso come questa

Così la prossima volta potrai ripetere tutto in modo rapido e sicuro.
