# WYE - Progress setup database PostgreSQL

Questo file tiene traccia delle attività da eseguire per preparare il backend e il database del progetto WYE.

## Stato verificato locale
- [x] PostgreSQL installato localmente
- [x] Servizio PostgreSQL attivo (`postgresql-x64-18`)
- [x] Accesso al server locale verificato con utente `postgres`
- [x] Credenziali salvate in `postgres/user_postgres.txt`

## Checklist di implementazione
- [x] Verifica ambiente PostgreSQL locale
- [x] Creazione del database `wye`
- [x] Esecuzione dello script SQL con le tabelle del modello WYE
- [x] Verifica presenza di tutte le tabelle principali
- [x] Verifica chiavi esterne e indici
- [ ] Preparazione eventuale seed iniziale di ingredienti/allergeni
- [ ] Collegamento del backend FastAPI al database
- [x] Test di insert/select di base

## Passo corrente
Il database WYE è stato creato correttamente e lo schema principale è stato applicato su PostgreSQL locale.

## Verifica eseguita
Sono state create 19 tabelle principali e un inserimento di test è riuscito correttamente nel database `wye`.

## Comandi da eseguire

1. Connettersi al server PostgreSQL locale
2. Creare il database `wye`
3. Eseguire `postgres/01_wye_schema.sql`
4. Verificare le tabelle con `\dt`
5. Verificare una query utile di prova

## Script SQL da usare
Il file `postgres/01_wye_schema.sql` contiene la struttura iniziale delle tabelle richieste dal progetto:
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

## Note di manutenzione
- Preferire un database dedicato `wye` invece della base `postgres`.
- Lasciare la base `postgres` come container amministrativo.
- I dati scientifici e gli ingredienti standard devono essere curati e validati prima di essere usati in produzione.
