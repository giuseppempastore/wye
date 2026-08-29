# Fase 5 — Validazione end-to-end

## Stato finale

La pipeline della Fase 5 è stata validata end-to-end sul branch `ingredients_score`, con commit di riferimento preesistente `96531041a89e6ce100d58f2f44ac2855a6989ecc` e worktree non ancora committato.

Alembic head finale: `0006_mapping_integrity_hardening`.

Giudizio: **FASE 5 COMPLETATA**.

## Architettura finale

La pipeline validata è:

`label_extraction_items`
→ `IngredientNormalizer`
→ `IngredientCandidateGenerator`
→ `IngredientMappingService`
→ `product_ingredients`
→ mapping review e candidate persistiti
→ deterministic resolver oppure human review
→ canonical `ingredients`
→ optional explicit reviewed alias approval.

Le responsabilità rimangono separate tra route FastAPI, service decisionale e repository PostgreSQL.

## Riepilogo Fasi 5.1–5.7

- 5.1: unicità materializzazione, singola review pending e constraint review/candidate.
- 5.2: normalizzazione deterministica `ingredient_normalization_v1`.
- 5.3: candidate canonical/accepted alias exact e fuzzy, con deduplica per canonical ingredient.
- 5.4: materializzazione atomica degli extraction item e persistenza della review.
- 5.5: auto-resolution esclusivamente per exact evidence univoca.
- 5.6: API di human review accepted/ambiguous/rejected.
- 5.7: approvazione alias esplicita, idempotente e auditabile.

## Ambiente di validazione

I test scriventi sono stati eseguiti esclusivamente su PostgreSQL locale `::1:5432`, database `wye_test`, verificato a `0006_mapping_integrity_hardening` prima dei test.

Il database predefinito `wye` non è stato usato per test scriventi. Tutte le variabili OpenAI/Gemini supportate sono state neutralizzate durante le suite offline.

## Scenario E2E

Lo scenario controllato crea la catena reale Fase 4: storage object, product image ingredients, image-derived label document, succeeded extraction run e ingredient extraction items ordinati.

### Exact canonical

`Acido Citrico` viene normalizzato a `acido citrico`, produce un exact canonical candidate, seleziona un solo candidate e termina automaticamente con review e product ingredient `accepted`.

### Exact accepted alias

L'alias accepted `e330 → Acido Citrico` risolve l'input `E 330`, normalizzato a `e330`, tramite exact accepted alias e deterministic auto-resolution.

### Fuzzy only

`Sodium benzoat` rispetto a `Sodium benzoate` produce un candidate fuzzy ma rimane `needs_review`, con `ingredient_id = NULL`, review pending e nessun selected candidate. Nessun fuzzy viene auto-accepted.

### Ambiguous exact

Due canonical ingredient distinti con canonical name normalizzato `ambiguous exact` producono due exact candidate. La review resta pending senza selezione; lingua, ranking e ID non determinano una scelta automatica.

### Zero candidate

Un testo sconosciuto controllato produce un product ingredient `needs_review`, review pending, zero candidate e `ingredient_id = NULL`.

## Human review

La review fuzzy viene accettata tramite `POST /ingredient-mapping-reviews/{review_id}/decision`. La validazione conferma:

- esattamente un candidate selezionato;
- review accepted e `reviewed_at` valorizzato;
- `reviewed_by = NULL`;
- product ingredient collegato al canonical corretto;
- `mapping_method = manual_review`;
- provenance `resolution_type = human_review`.

Le decisioni ambiguous e rejected sono state eseguite tramite la stessa API e lasciano `ingredient_id = NULL`, nessuna selezione, status coerenti e provenance umana.

## Reviewed alias approval

L'alias viene creato solo tramite `POST /ingredient-mapping-reviews/{review_id}/approve-alias` dopo l'accepted manuale.

Sono stati verificati raw name, normalized alias, lingua, canonical ingredient, `accepted`, `manual_review`, confidence numerica `1.0`, `is_primary = false`, timestamp e provenance collegata a review/product ingredient/extraction item.

`PostgresIngredientCatalogRepository` carica naturalmente il nuovo alias accepted.

## Future mapping tramite alias

Dopo l'approvazione di `sodium benzoat`, un nuovo extraction item con la stessa forma viene elaborato dal normale Mapping Service. Il candidate generator trova l'exact accepted alias e il deterministic resolver lo auto-accetta verso il canonical ingredient corretto.

Una review pending creata prima dell'alias rimane invariata: non avvengono remapping, candidate regeneration o auto-accept retroattivi.

## Provenance traversal

Una query PostgreSQL ricostruisce la catena:

`product → product_ingredient → ingredient → mapping review → selected candidate → extraction item → extraction run → label document → product image`.

Sono verificati raw text, normalized text, normalization version, candidate generation version, deterministic resolution version/type, selected candidate, canonical ingredient, extraction item e extraction run.

## Idempotenza

Il rerun del Mapping Service sullo stesso extraction run non crea nuovi product ingredient, review o candidate e non modifica decisioni terminali. La repeated alias approval restituisce il medesimo alias con `created = false`.

## Constraint

Sono stati verificati senza disabilitarli:

- unicità non-null `label_extraction_item_id`;
- una sola review pending per product ingredient;
- review accepted con esattamente un selected candidate;
- candidate canonical ingredient only;
- unicità alias accepted per normalized alias e lingua.

## Concorrenza

Le regressioni coprono:

- due Mapping Service concorrenti sullo stesso extraction item;
- due human decision concorrenti sulla stessa review, con un vincitore e un conflict;
- due alias approval concorrenti sulla stessa review, convergenti a un alias (`created=true` e `created=false`).

## Migration lifecycle

Su database temporaneo dedicato `wye_phase58_lifecycle_1605849d9a0f`:

- upgrade iniziale a `0005_label_extraction_pipeline`;
- `0005 → 0006` riuscito;
- `0006 → 0005` riuscito;
- `0005 → 0006` riuscito;
- head finale verificato a `0006_mapping_integrity_hardening`;
- database temporaneo rimosso.

Nessun database storico è stato sottoposto a downgrade.

## Risultati suite

- Scenario E2E e API regression immediata: 8 test, tutti passati.
- Suite Fasi 5.1–5.8: 110 test, tutti passati, 1 lifecycle test legacy skipped perché gated separatamente.
- Suite backend offline: 162 test, tutti passati, 71 integrazioni condizionali skipped.
- `py_compile`: riuscito.
- `git diff --check`: riuscito; restano solo warning informativi LF/CRLF.
- Nessuna chiamata AI reale durante la validazione.

## Bug emerso e fix minimo

La risposta approve-alias serializzava `confidence NUMERIC(4,3)` come stringa (`"1.000"`) perché `alias` era dichiarato come dizionario generico. È stato introdotto un response model Pydantic tipizzato, che espone correttamente `confidence` come numero `1.0`. Il test E2E costituisce la regression coverage.

## Limiti e rischi residui

- L'autenticazione rimane la protezione temporanea `X-Wye-Image-Key`; non esiste ancora identity/authorization reviewer definitiva.
- Un alias senza detected language non può essere approvato, per evitare di inventare una lingua richiesta dallo schema.
- Alias deprecated o legacy richiedono intervento separato e non vengono promossi automaticamente.
- Il worktree deve ancora essere revisionato e committato esplicitamente dall'utente.

## Fuori scope confermato

Non sono stati implementati EFSA, OpenFoodTox, scientific assessments, scoring, nutrition scoring, frontend Flutter, auth definitiva, AI mapping, embeddings, vector database, translation, automatic alias learning, candidate regeneration, review reopen o creazione di canonical ingredient.

## Criteri di completamento

La Fase 5 è completata perché tutti i percorsi exact/fuzzy/ambiguous/zero-candidate sono coerenti, le decisioni automatiche e umane sono atomiche, l'alias approval è esplicita, il nuovo alias abilita esclusivamente mapping futuri, provenance/idempotenza/concorrenza sono verificabili, i constraint restano attivi, il lifecycle 0005↔0006 è reversibile e tutte le suite pertinenti passano.
