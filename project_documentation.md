# WYE - Documentazione completa di progetto

Questo documento è pensato come memoria di progetto per futuri assistenti, agenti, sviluppatori e collaboratori. Deve permettere a una nuova sessione di capire rapidamente:
- che problema risolve il prodotto
- come è strutturato il sistema
- come funziona lo scoring
- come sono pensate le tabelle SQL
- quali sono le regole di business e di prodotto
- come distinguere alimenti e cosmetici
- come gestire la parte free e premium

Il documento è in italiano e raccoglie la logica finale che è stata stabilita.

---

## 1. Obiettivo del prodotto

L’app vuole valutare la salubrità e la qualità di un prodotto in modo trasparente e comprensibile.

Il sistema deve essere in grado di rispondere a domande come:
- questo alimento è sano?
- questo alimento ha una tabella nutrizionale positiva?
- questo alimento contiene ingredienti problematici?
- questo cosmetico è sicuro dal punto di vista della composizione?
- questo prodotto contiene allergeni?
- quale punteggio finale ottiene il prodotto?

Il prodotto non deve essere pensato come “AI che decide se è sano a caso”, ma come:
- database di prodotti
- database di ingredienti canonicalizzati
- database di evidenze scientifiche
- database di allergeni
- motore di scoring chiaro e tracciabile
- catalogo di valori nutrizionali dichiarati dal produttore

---

## 2. Principio fondamentale di business

Il sistema deve separare chiaramente due livelli di valutazione:

### 2.1 Alimenti
Per gli alimenti ci sono due dimensioni separate:
1. Ingredient score
2. Nutrition score
3. Final food score

### 2.2 Cosmetici
Per i cosmetici non esiste scoring nutrizionale.
Viene valutato solo l'ingredient score, cioè la miscela di ingredienti.

Questo è necessario perché:
- una tabella nutrizionale non ha senso per un cosmetico
- la valutazione del cosmetico va fatta sul profilo della composizione
- i cosmetici non vengono valutati in base a calorie, zuccheri, grassi, ecc.

---

## 3. Regola chiave di scoring

La regola più importante è questa:

Per gli alimenti, anche se i valori nutrizionali sono ottimi, ma gli ingredienti sono potenzialmente ad alto rischio, il punteggio finale del prodotto viene penalizzato in modo molto forte, fino a essere sostanzialmente “sovrascritto” dal rischio degli ingredienti.

Questo significa che:
- nutrition score può essere alto / verde
- ingredient score può essere basso / rosso
- final score sarà basso / rosso

La logica è:
- la nutrizione misura la qualità quantitativa del prodotto
- gli ingredienti misurano la qualità qualitativa della composizione
- gli ingredienti critici hanno peso dominante nella valutazione finale

### Esempio
Un prodotto può avere:
- calorie basse
- zuccheri bassi
- sale basso
- grassi saturi contenuti
- fibre buone

Ma avere ingredienti come:
- conservanti artificiali con allerta
- additivi sospetti
- oli altamente raffinati
- dolcificanti critici
- ingredienti con rischio elevato

In questo caso:
- nutrition score = buono
- ingredient score = basso
- final score = basso

Il risultato finale non deve essere un “compensazione” automatico. I componenti pericolosi devono avere priorità.

---

## 4. Distinzione tra free e premium

### 4.1 Base gratuita
L’app per utenti base deve essere semplice e rapida.

Deve usare principalmente:
- barcode scan
- lookup del prodotto nel database
- visualizzazione del risultato

Deve fare soltanto:
- score di salubrità generale
- ingredienti critici
- allergeni rilevati
- valutazione nutrizionale semplice se è un alimento
- nessun login obbligatorio
- nessuna pubblicità
- nessun obbligo di registrazione

### 4.2 Premium
La versione premium include tutto ciò che è più avanzato e personalizzato:
- input manuale degli ingredienti
- foto della lista ingredienti
- foto della tabella nutrizionale
- inserimento manuale dei valori nutrizionali
- profilazione utente:
  - altezza
  - peso
  - BMI
  - allergie
  - patologie
  - obiettivi nutrizionali
  - restrizioni dietetiche
- score personalizzato per l’utente
- raccomandazioni personalizzate
- logica di warning in base alla sensibilità personale

Quindi:
- base = barcode-only, semplice, veloce, gratuito
- premium = approfondimento, personalizzazione, input manuale, dati personali

---

## 5. Categorie di prodotto

Il sistema deve distinguere almeno queste macro categorie:

### 5.1 Alimenti
- bevande
- snack
- dolciumi
- prodotti da forno
- condimenti
- latticini
- carne e affettati
- cereal foods
- preparati pronti
- surimi e prodotti trasformati

Per gli alimenti si usano:
- ingredient score
- nutrition score
- final food score

### 5.2 Cosmetici
- creme
- detergenti
- lozioni
- shampoo
- balsami
- sieri
- makeup
- prodotti per la cura della pelle

Per i cosmetici si usa:
- ingredient score
- no nutrition score

### 5.3 Potenziali future categorie
- integratori
- nutraceutici
- erboristeria
- prodotti per animali
- prodotti freschi e surgelati

---

## 6. Architettura funzionale

Il sistema deve essere progettato così:

### 6.1 Frontend / App
- scansione barcode
- OCR da foto
- inserimento manuale
- mostrare risultato prodotto
- mostrare score, allergeni, ingredienti critici, motivazioni

### 6.2 Backend API
- riceve barcode o testo
- cerca nel database prodotto
- trova ingredienti e nutrizione associati
- calcola score
- restituisce risultato in JSON

### 6.3 Database SQL
- prodotti
- ingredienti
- alias / sinonimi
- classificazioni
- nutrienti
- allergeni
- evidenze scientifiche
- score
- utenti premium
- profili personalizzati

### 6.4 Pipeline di normalizzazione
- ricevi ingredient stringa
- normalizza la stringa
- detect language
- match alias/sinonimi
- map to canonical ingredient
- assegna confidence
- calcola ingredient score
- recupera nutrient data se disponibile
- calcola nutrition score
- calcola final score

---

## 7. Regole di prodotto per gli alimenti

### 7.1 Ingredient score
Valuta la qualità degli ingredienti presenti.

Tiene conto di:
- additivi potenzialmente problematici
- conservanti
- dolcificanti
- coloranti
- esaltatori di sapidità
- oli trasformati
- ingredienti ultra-processati
- ingredienti con allerta scientifica
- ingredienti allergenici

L’ingredient score non si basa sul gusto o sulla percezione del consumatore, ma su:
- rischio per ingredienti
- evidenza
- classificazione tossicologica
- allergenicità
- categoria dell’ingrediente

### 7.2 Nutrition score
Valuta la tabella nutrizionale dichiarata dal produttore.

I campi principali sono:
- kcal / energia
- proteine
- carboidrati
- zuccheri
- grassi totali
- grassi saturi
- sodio
- fibre
- porzione
- valori per 100g o 100ml

Questo score è basato sulle soglie nutrizionali e sulle linee guida pubbliche.

### 7.3 Final food score
È la sintesi finale di ingredient score e nutrition score.

La regola generale è:
- se ingredient score è molto basso, il final score viene fortemente penalizzato
- la nutrizione non può compensare totalmente il rischio forte degli ingredienti

Formula concettuale:

final_food_score = (ingredient_score * 0.60) + (nutrition_score * 0.40)

ma con regola di penalizzazione:

if ingredient_score < 35 and ingredient_risk_level in ["high", "critical"]:
    final_food_score = min(final_food_score, 35)

oppure una penalizzazione ancora più forte se il prodotto contiene ingredienti molto critici.

Questo rende il sistema più realistico e molto più credibile rispetto a un semplice sommatorio.

---

## 8. Regole di prodotto per i cosmetici

Per i cosmetici il modello è semplificato.

Non si guarda a:
- calorie
- zuccheri
- grassi saturi
- sale
- fibre

Si guarda invece a:
- ingredienti con rischio irritante
- allergeni
- conservanti potenti
- oli essenziali
- fragranze
- parabeni
- sulfati
- coloranti
- composti tossicologicamente problematici
- presenza di ingredienti a rischio per pelle

### Cosmetici score formula
final_cosmetic_score = ingredient_score

Non ci sono nutrizione e tabellina dichiarata.

---

## 9. Allergeni

Gli allergeni devono essere gestiti come parte della valutazione ingredientale.

### 9.1 Allegato per prodotto
L’utente deve sempre poter vedere:
- allergeni contenuti
- allergeni potenzialmente presenti
- allergeni sospetti
- allergeni non dichiarati ma rilevati tramite mapping

### 9.2 Tipi di stato allergenico
- contains
- may_contain
- suspected
- unknown

### 9.3 Esempi di allergeni principali
- glutine
- latte
- uova
- arachidi
- noci
- soia
- sesamo
- sedano
- senape
- pesce
- crostacei
- molluschi
- sulfiti
- kiwi
- frutta a guscio

### 9.4 Visualizzazione UX
- icona allergene con nome
- label “contiene” o “potenziale contaminazione”
- colore differenziato
- notifica se è in contrasto con il profilo personale del premium utente

---

## 10. Barcode-first architecture

Per gli alimenti, la scelta strategica è chiara:
- usare sempre il barcode come riferimento primario
- creare un database di prodotti reali
- salvare ingredienti e nutrienti per prodotto
- evitare di fare parsing manuale senza catalogo per default

### 10.1 Flusso base
1. utente scansiona barcode
2. backend cerca prodotto per barcode
3. se trovato:
   - carica ingredient list
   - carica nutrition facts
   - calcola ingredient score
   - calcola nutrition score
   - calcola final food score
   - restituisce risultato
4. se non trovato:
   - utente base vede “prodotto non presente nel catalogo”
   - premium può inserire manualmente dati

### 10.2 Flusso premium manuale
Premium può inserire:
- ingredient list manually
- ingredient list from photo
- nutrition facts from photo
- nutrition facts manually entered
- prodotto creato come record nuovo
- flag “needs_review”
- review da parte di admin o moderation

Il barcode del prodotto nuovo viene salvato e, se validato, entra nel database.

---

## 11. Struttura database: tabelle principali

Di seguito è la struttura logica del database, con i campi principali e la loro funzione.

### 11.1 Tabella: products
Questa tabella identifica il prodotto reale.

Colonne principali:
- id: PK
- barcode: codice a barre principale, unico per prodotto
- gtin: GTIN esteso, opzionale
- brand_name: nome del marchio
- product_name: nome del prodotto
- category: categoria (food, cosmetic, beverage, etc.)
- product_type: sotto categoria (snack, shampoo, yogurt, etc.)
- source: sorgente dati (manual, API, OCR, imported)
- verified: flag se il prodotto è verificato
- version: versione del record
- status: active, draft, needs_review, archived
- created_at
- updated_at

Ruolo:
- identifica il prodotto reale
- collega ingredienti e valori nutrizionali
- è l’entità centrale del catalogo

---

### 11.2 Tabella: ingredients
Questa tabella rappresenta il catalogo centrale degli ingredienti.

Colonne principali:
- id: PK
- canonical_name: nome standard, esempio: sodium benzoate
- ingredient_group: category generale, es. sweetener, preservative, colorant, oil, allergen
- risk_level: low, moderate, high, critical
- allergen_flag: boolean
- evidence_level: livello di evidenza
- cas_number: opzionale
- einecs_number: opzionale
- common_name: nome comune, se presente
- status: active / deprecated / review_pending
- created_at
- updated_at

Ruolo:
- definisce l’ingrediente standard
- collega alias, evidenze e classificazioni

---

### 11.3 Tabella: ingredient_aliases
Questa tabella contiene tutti i nomi alternativi di un ingrediente.

Colonne principali:
- id: PK
- ingredient_id: FK -> ingredients.id
- alias_name: nome alternativo
- normalized_alias: alias normalizzato
- language: it, en, fr, es, de, etc.
- alias_type: synonym, translation, code, e_number, trade_name
- confidence: livello di confidenza del mapping
- is_primary: boolean
- created_at

Ruolo:
- mappare una stringa del packaging al canonical ingredient
- risolvere lingue diverse
- tradurre E-numbers e sinonimi

---

### 11.4 Tabella: ingredient_categories
Questa tabella classifica l’ingrediente in categorie.

Colonne principali:
- id: PK
- ingredient_id: FK -> ingredients.id
- category_name: preservative, sweetener, emulsifier, fragrance, colorant, essential oil, allergen, etc.
- classification_source: internal, scientific, regulatory
- created_at

Ruolo:
- permette di filtrare ingredienti per tipologia
- supporta il scoring di ingredienti e l’analisi di rischio

---

### 11.5 Tabella: ingredient_risk_profiles
Questa tabella contiene i dettagli di rischio dell’ingrediente.

Colonne principali:
- id: PK
- ingredient_id: FK -> ingredients.id
- risk_level: low, moderate, high, critical
- hazard_type: allergen, endocrine, carcinogenic, irritant, oxidant, contaminant, etc.
- evidence_level: 1..6 o equivalente
- adverse_risk_note: testo breve
- noael: opzionale
- adi: opzionale
- dose_threshold_low: opzionale
- dose_threshold_high: opzionale
- population_at_risk: testo libero o JSON
- review_status: approved, pending_review, disputed
- updated_at

Ruolo:
- definisce il rischio specifico dell’ingrediente
- fornisce dettagli scientifici da usare nel scoring

---

### 11.6 Tabella: allergens
Questa tabella contiene la lista standard degli allergeni dichiarati e riconosciuti.

Colonne principali:
- id: PK
- allergen_name: esempio gluten, milk, peanuts
- canonical_code: standard code, se usato
- category: cereals, dairy, nuts, seafood, etc.
- description: testo breve
- is_active: boolean
- created_at

Ruolo:
- centralizzare i nomi e le categorie allergeniche
- permettere mapping rapido con ingredienti

---

### 11.7 Tabella: ingredient_allergens
Questa tabella collega ingredienti e allergeni.

Colonne principali:
- id: PK
- ingredient_id: FK -> ingredients.id
- allergen_id: FK -> allergens.id
- relationship_type: contains, may_contain, suspected, derived_from
- confidence: livello di certezza
- notes: testo libero

Ruolo:
- evitare di hardcodare gli allergeni in ingredienti
- supportare mapping multiplo e robusto

---

### 11.8 Tabella: sources
Questa tabella contiene le fonti autoritative e scientifiche.

Colonne principali:
- id: PK
- source_name: EFSA, WHO, FDA, PubMed, JECFA, IARC, etc.
- source_type: regulatory, public_health, scientific, academic
- url: link
- authority_level: 1..6
- country: ISO country code
- is_authoritative: boolean
- created_at

Ruolo:
- centralizzare la validazione scientifica
- permettere la tracciabilità di ogni rischio

---

### 11.9 Tabella: ingredient_evidence
Questa tabella collega ingredienti e fonti scientifiche.

Colonne principali:
- id: PK
- ingredient_id: FK -> ingredients.id
- source_id: FK -> sources.id
- evidence_title: titolo della pubblicazione o documento
- evidence_summary: sintesi
- risk_statement: frase esplicativa
- evidence_level: livello di evidenza
- url: link
- publication_date
- created_at

Ruolo:
- per ogni ingrediente, il sistema deve avere evidenze
- permette di mostrare “perché questo score?” all’utente

---

### 11.10 Tabella: product_ingredients
Questa è la tabella più importante per il mapping prodotto-ingredienti.

Colonne principali:
- id: PK
- product_id: FK -> products.id
- ingredient_id: FK -> ingredients.id
- raw_name: stringa originale della confezione
- canonical_name: nome normalizzato
- position_in_list: ordine nella lista ingredienti
- confidence: livello di confidenza del mapping
- allergen_flag: boolean
- risky_flag: boolean
- is_unknown: boolean
- manual_override: boolean
- created_at

Ruolo:
- indica che un prodotto contiene un dato ingrediente
- collega ogni prodotto all’ingrediente canonicalizzato
- consente di avere un ingredient score per prodotto

---

### 11.11 Tabella: nutrition_facts
Questa tabella contiene la tabellina nutrizionale dichiarata dal produttore.

Colonne principali:
- id: PK
- product_id: FK -> products.id
- serving_size: esempio 100g, 250ml
- energy_kcal: kcal per porzione o per 100g
- protein_g
- carbs_g
- sugar_g
- fat_g
- saturated_fat_g
- sodium_mg
- fiber_g
- source: dichiarazione produttore / API / manuale / OCR
- declared_by_manufacturer: boolean
- verified: boolean
- raw_text: testo grezzo della tabella
- created_at
- updated_at

Ruolo:
- salvare i valori nutrizionali ufficiali del prodotto
- permettere il nutrition score
- supportare confronto con soglie nutrizionali

---

### 11.12 Tabella: nutrition_thresholds
Questa tabella contiene le soglie nutrizionali delle linee guida.

Colonne principali:
- id: PK
- category: food category
- nutrient_name: sugar, sodium, saturated_fat, calories, fiber
- threshold_low
- threshold_medium
- threshold_high
- unit
- source_reference
- valid_from
- valid_to

Ruolo:
- dare regole standard per valutare se un nutriente è basso / medio / alto
- rendere il sistema trasparente e standardizzato

---

### 11.13 Tabella: product_scores
Questa tabella salva il punteggio finale del prodotto.

Colonne principali:
- id: PK
- product_id: FK -> products.id
- ingredient_score: 0-100
- nutrition_score: 0-100
- final_score: 0-100
- score_band: excellent, good, moderate, poor, critical
- ingredient_risk_summary: testo breve
- nutrition_summary: testo breve
- final_summary: testo breve
- calculation_version: versione dell’algoritmo di scoring
- generated_at

Ruolo:
- salvare il risultato finale
- permettere il confronto tra prodotti
- supportare la cache e la revisione

---

### 11.14 Tabella: cosmetics_products
Questa tabella è specifica per i cosmetici.

Colonne principali:
- id: PK
- barcode: opzionale
- brand
- product_name
- product_type
- ingredient_list_raw
- ingredients_mapped: boolean
- ingredient_score: 0-100
- final_score: 0-100
- verified: boolean
- created_at
- updated_at

Ruolo:
- gestire prodotti cosmetici separatamente dal catalogo alimentare
- supportare il modello di scoring senza nutrizione

---

### 11.15 Tabella: cosmetic_ingredient_assessment
Questa tabella collega prodotto cosmetico e ingredienti, con valutazione specifica.

Colonne principali:
- id: PK
- cosmetic_product_id: FK -> cosmetics_products.id
- ingredient_id: FK -> ingredients.id
- risk_level: low / moderate / high / critical
- reason: testo breve
- confidence: 0-1
- created_at

Ruolo:
- analisi del livello di rischio per ingredienti del cosmetico
- supportare la valutazione finale del prodotto cosmetico

---

### 11.16 Tabella: users
Questa tabella rappresenta gli utenti.

Colonne principali:
- id: PK
- email: opzionale se utente anonimo
- auth_provider: google, email, anonymous
- is_premium: boolean
- created_at

Ruolo:
- gestione utenti premium e base
- supporta eventuale personalizzazione

---

### 11.17 Tabella: user_profiles
Questa tabella contiene i dati fisiologici dell’utente premium.

Colonne principali:
- id: PK
- user_id: FK -> users.id
- age
- height_cm
- weight_kg
- bmi
- allergies_raw
- health_conditions_raw
- diet_type
- activity_level
- goal_type
- created_at
- updated_at

Ruolo:
- personalizzare il punteggio per utenti premium
- adattare il risultato a problemi come diabete, sovrappeso, allergie, dieta, ecc.

---

### 11.18 Tabella: user_allergies
Questa tabella salva le allergie dell’utente premium.

Colonne principali:
- id: PK
- user_id: FK -> users.id
- allergen_id: FK -> allergens.id
- severity: mild, moderate, severe
- notes

Ruolo:
- personalizzare gli alert per allergeni
- migliorare il warning su prodotti critici per quell’utente

---

### 11.19 Tabella: product_reviews
Questa tabella salva i prodotti aggiunti manualmente o validati in review.

Colonne principali:
- id: PK
- product_id: FK -> products.id
- submitted_by_user_id: FK -> users.id
- review_status: pending, approved, rejected
- source_type: manual_input, OCR, barcode
- reason: testo
- created_at

Ruolo:
- gestire i prodotti non presenti nel database
- permettere la validazione del contenuto inserito dall’utente premium

---

## 12. Regole del scoring per alimenti

Le regole devono essere sempre spiegabili.

### 12.1 Ingredient score
L’ingredient score deve valutare la composizione.

Esempi di penalità:
- ingredienti a rischio alto = grande penalty
- additivi critici = penalty moderata o alta
- ingredienti ultra-processati = penalty
- allergeni pronunciati = penalty forte
- ingredienti sconosciuti = warning e rischio di downgrade

### 12.2 Nutrition score
Il nutrition score va valutato su parametri come:
- zuccheri
- sali
- grassi saturi
- calorie
- fibre
- proteine

Se la nutrizione è positiva ma gli ingredienti sono problematici, la nutrizione non salva il prodotto.

### 12.3 Final food score
Il final score deve essere il risultato finale di una logica che mette prima la qualità dell’ingrediente e poi la qualità nutrizionale.

Esempio di regola:

if ingredient_score <= 35:
    final_score = min(final_score, 35)

oppure regola più dettagliata:

if ingredient_score < 40 and contains_high_risk_ingredient:
    final_score = final_score * 0.6

Il punto importante è che il rischio degli ingredienti non sia “sommato in modo neutro” ma abbia effetto dominante.

---

## 13. Regole di classificazione del punteggio

Il risultato del prodotto deve essere mostrato in un bucket chiaro:

- 0-24: critical / molto basso
- 25-39: poor / scarso
- 40-59: moderate / medio
- 60-79: good / buono
- 80-100: excellent / eccellente

Questo deve essere applicato anche a:
- ingredient score
- nutrition score
- final score

---

## 14. Esposizione al cliente

L’app deve mostrare sempre in modo leggibile:
- score finale
- ingredient score
- nutrition score
- ingredienti critici
- allergeni rilevati
- motivi del punteggio
- evidenze scientifiche / fonti

### Esempio di output UX
- Final score: 34/100 (rosso)
- Nutrition score: 82/100 (verde)
- Ingredient score: 26/100 (rosso)
- Main concerns:
  - artificial preservatives
  - high-risk sweetener
  - processed oils
  - allergens detected

Questo rende chiaro che:
- la tabella nutrizionale è buona
- ma la composizione è problematica
- quindi il prodotto finale è basso

---

## 15. Principi di qualità scientifica

Il sistema non può basarsi su ai generica senza evidenza.

### 15.1 Cosa può fare l’AI
- OCR
- riconoscimento di testo
- language detection
- parsing ingredient list
- matching alias
- mapping to canonical ingredient
- supporto nel processo di normalizzazione

### 15.2 Cosa non deve fare l’AI
- dichiarare “sicuro” o “pericoloso” senza fonte
- sostituire il database scientifico
- inventare evidenze
- usare informazioni non curate come fonte di verità

Il database scientifico e strutturato è l’autorità finale.

---

## 16. Gestione di linguaggio e normalizzazione

Il sistema deve usare una lingua canonica per ingredienti, preferibilmente in inglese, per il mapping standard.

Esempi:
- “sodio benzoato” -> sodium benzoate
- “E330” -> citric acid
- “burro di cacao” -> cocoa butter

Da ogni list ingredienti del packaging, il workflow è:
1. detect language
2. clean text
3. normalize tokens
4. search alias table
5. map to canonical ingredient
6. assign confidence score
7. attach to product_ingredients
8. compute ingredient score

---

## 17. Logica di accesso e feature per tipo di utente

### 17.1 Utente base
- barcode scan
- risultato rapido
- senza login
- semplice da usare
- no personal profile
- no manual insert obbligatorio

### 17.2 Utente premium
- manual ingredient insertion
- photo upload
- nutrition data input
- advanced explanation
- score personalizzato
- health profile aware output
- allergen personalization

---

## 18. Esempio di risultato finale generico

Esempio per alimento:

- product: brand X, product Y
- barcode: valid
- ingredient score: 32/100
- nutrition score: 81/100
- final score: 38/100
- status: poor
- reasons:
  - high-risk additives present
  - processed ingredients
  - low ingredient quality
  - allergens detected
- nutrition notes:
  - good sugar profile
  - moderate sodium
  - acceptable calories
- conclusion:
  - nutrizionalmente abbastanza valido
  - ma la miscela è problematica
  - punteggio finale basso

Questo è esattamente il tipo di risultato che mostra il principio del “nutrizione buona ma ingredienti cattivi”.

---

## 19. Esempio di risultato cosmetico

- product: shampoo X
- ingredient score: 53/100
- nutrition score: not applicable
- final score: 53/100
- concerns:
  - fragrance ingredients
  - irritants
  - preservative with risk concerns
- conclusion:
  - no nutrition score
  - assessed only on ingredient profile

---

## 20. Regola finale per il team di sviluppo

Il progetto va pensato così:

1. Alimenti
   - ingredient score
   - nutrition score
   - final score
   - barcode first
   - premium handles manual insertion

2. Cosmetici
   - ingredient score only
   - no nutrition score
   - barcode first if available

3. Free / base
   - barcode-only
   - no login
   - no ads
   - fast scoring

4. Premium
   - manual input
   - profile personalization
   - advanced alerts and score recomputation

5. Priority principle
   - ingredient risk can dominate final scoring
   - nutrition quality can be green, but cannot rescue critical composition problems

---

## 21. Output strategico da tenere sempre in mente

Il sistema non deve essere un “AI che giudica il cibo”, ma un sistema di:
- catalogazione dei prodotti
- catalogazione degli ingredienti
- evidenza scientifica
- scoring critico e trasparente
- benchmarking di qualità prodotto
- personalizzazione premium

Questa è la vera direzione del progetto.

---

## 22. Descrizione sintetica per future sessioni AI

Se una nuova sessione di agent deve capire il progetto in una frase:

“WYE è un motore di valutazione della salubrità dei prodotti dove gli alimenti vengono valutati su ingredienti e nutrizione, i cosmetici solo sugli ingredienti, il barcode è la chiave primaria per la base gratuita, il premium permette input manuale e personalizzazione, e i rischi degli ingredienti possono sovrascrivere completamente un buon profilo nutrizionale, generando un punteggio finale basso e rosso.”

---

## 23. Linee guida per il database SQL

Il database deve essere pensato così:
- products = catalogo prodotto
- ingredients = catalogo ingrediente standard
- ingredient_aliases = sinonimi e mapping linguistico
- ingredient_risk_profiles = rischio di ingredienti
- allergens = allergeni standard
- ingredient_allergens = relazione ingrediente-allergene
- sources = fonti scientifiche
- ingredient_evidence = evidenze per ingrediente
- product_ingredients = ingredienti di un prodotto
- nutrition_facts = tabella nutrizionale del prodotto
- product_scores = score calcolati
- users = utenti
- user_profiles = profilo personale premium
- user_allergies = allergie dell’utente
- cosmetics_products = prodotti cosmetici
- cosmetic_ingredient_assessment = ingredient score per cosmetici

---

## 24. Regola da non perdere mai

Se l’ingrediente è pericoloso, la composizione può avere un punteggio basso anche quando la nutrizione è buona.

Questo è uno dei principi più importanti del progetto.

---

## 25. Checklist finale per implementazione

Prima di iniziare a costruire il backend e il database, verificare sempre:
- [ ] c’è distinzione chiara tra alimenti e cosmetici
- [ ] ingredient score esiste per entrambi
- [ ] nutrition score esiste solo per alimenti
- [ ] barcode è la chiave primaria per il free
- [ ] manual input è solo per premium
- [ ] allergeni sono trattati come parte degli ingredienti
- [ ] il final score è penalizzato da ingredienti critici
- [ ] i dati scientifici sono collegati a fonti
- [ ] il sistema usa catalogo standard, non AI ad hoc come fonte di verità

---

## 26. Conclusione

Il progetto è stato stabilizzato in una logica solida:
- alimenti: ingredient + nutrizione + final score
- cosmetici: ingredient score only
- base: barcode-only, gratuito, semplice
- premium: manual input, personalizzazione, score su misura
- ingredient criticality può sovrascrivere la bontà nutrizionale

Questo è il modello migliore per costruire un prodotto credibile, comprensibile e sostenibile.
