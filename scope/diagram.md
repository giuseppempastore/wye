┌─────────────────────┐
│   Flutter (mobile)  │
│                     │
│  1. Camera app      │
│  2. Scan barcode    │
│  3. Extract code    │
│     (es. 8718206...)│
└──────────┬──────────┘
           │
           │ HTTP GET
           │ /product/8718206...
           ▼
┌─────────────────────┐
│  Python (backend)   │
│                     │
│  1. Ricevi barcode  │
│  2. Query DB        │
│  3. Trova product   │
│  4. Calcola score   │
│  5. Return JSON     │
└──────────┬──────────┘
           │
           │ JSON response
           │ {score, ingredients...}
           ▼
┌─────────────────────┐
│   Flutter (mobile)  │
│                     │
│  1. Ricevi JSON     │
│  2. Parse dati      │
│  3. Mostra UI       │
└─────────────────────┘