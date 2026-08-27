Analizza completamente il repository Wye.

NON modificare alcun file.

Voglio che tu faccia un audit tecnico dell'intero progetto, con particolare attenzione a:
- backend
- PostgreSQL/schema
- ingredienti
- ingredient aliases
- ingredient evidence
- ingredient risk profiles
- product scoring
- test
- script di seed/import
- eventuali sistemi di migration

Il nuovo obiettivo del progetto è costruire un sistema evidence-based per la valutazione degli ingredienti, basato inizialmente su EFSA/OpenFoodTox e fonti regolatorie ufficiali.

Leggi anche WYE_TODO_EFSA.md se presente.

NON implementare ancora nulla e NON inventare una metodologia di scoring.

Restituisci:
1. architettura attuale
2. cosa possiamo riutilizzare
3. cosa va modificato
4. quali nuove tabelle/componenti servono
5. eventuali problemi architetturali
6. un piano di implementazione ordinato

Non fare modifiche al repository.