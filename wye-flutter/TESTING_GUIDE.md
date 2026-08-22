# GUIDA COMPLETA AL TESTING - WYE Flutter App

## 📋 Prerequisiti

### 1. Setup Backend Python
```bash
cd c:\Projects\wye\backend

# Crea venv
python -m venv venv
.\venv\Scripts\Activate.ps1

# Installa dipendenze
pip install -r requirements.txt

# Avvia il server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Il backend deve essere in esecuzione su:
- **Android Emulator**: `http://10.0.2.2:8000`
- **iOS Simulator**: `http://127.0.0.1:8000`
- **Device Fisico**: `http://YOUR_LOCAL_IP:8000` (es. `http://192.168.1.100:8000`)

### 2. Setup Flutter
```bash
cd c:\Projects\wye\wye-flutter

# Installa dipendenze
flutter pub get

# Pulisci build precedenti
flutter clean

# Verifica setup
flutter doctor
```

---

## 🧪 Test Opzioni

### Opzione 1: Emulator Android (Consigliato per MVP)

#### 1.1 Avviare l'emulator
```bash
# Elenca device disponibili
flutter emulators

# Avvia emulator predefinito
flutter emulators --launch <emulator_name>

# Oppure da Android Studio: Device Manager
```

#### 1.2 Aggiornare IP Backend
Nel file `lib/services/api_client.dart`:
```dart
class ApiConfig {
  static const String baseUrl = 'http://10.0.2.2:8000';  // Android emulator
}
```

#### 1.3 Eseguire l'app
```bash
flutter run
```

L'app si connetterà a `http://10.0.2.2:8000` (IP speciale per emulator → host machine).

#### 1.4 Testare con barcode di test
```
Prova questi barcode:
- 5901234123457 (test EAN)
- 8718206112001 (Nutella reale)
- 4006381333931 (test EAN)
```

### Opzione 2: Device Fisico Android

#### 2.1 Preparare device
```powershell
# Abilita USB Debugging
Settings → Developer Options → USB Debugging (ON)

# Collega via USB al computer

# Verifica che il device sia riconosciuto
adb devices

# Concedi permessi on-screen quando appare il prompt
```

#### 2.2 Trovare IP locale del tuo computer
```powershell
# Su Windows
ipconfig

# Cerca "IPv4 Address" nella sezione WiFi
# Es: 192.168.1.100
```

#### 2.3 Aggiornare IP Backend
```dart
class ApiConfig {
  static const String baseUrl = 'http://192.168.1.100:8000';  // Sostituisci con il TUO IP
}
```

#### 2.4 Eseguire l'app
```bash
flutter run
```

### Opzione 3: iOS Simulator

#### 3.1 Avviare il simulator
```bash
open -a Simulator
```

#### 3.2 Aggiornare IP Backend
```dart
class ApiConfig {
  static const String baseUrl = 'http://127.0.0.1:8000';  // iOS simulator
}
```

#### 3.3 Eseguire l'app
```bash
flutter run -d ios
```

### Opzione 4: iOS Device Fisico

Richiede certificati Apple e provisioning profile.

```bash
flutter run -d <device_id>
```

---

## 🔍 Testing Scenarios

### Scenario 1: Scansione Barcode Esistente

**Setup:**
1. Avvia backend Python con `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. Avvia app Flutter: `flutter run`
3. Vai a Home → "Scansiona Barcode"

**Test:**
```
1. Inserisci barcode: 8718206112001 (Nutella)
2. Clicca "Cerca Prodotto"
3. ❌ Se vedi: "Prodotto non trovato"
   → Il database backend è vuoto
   → Popola il DB con seed_db.py

4. ✅ Se vedi: Schermata risultati con score
   → Score Ingredienti, Nutrizione, Finale
   → Allergeni (se presenti)
   → SUCCESS!
```

**Debug:**
```bash
# Nel terminal dell'app Flutter, leggi i log:
I/flutter ( 1234): 📦 Fetching product for barcode: 8718206112001
I/flutter ( 1234): ✅ Product found: Nutella

# Se vedi errore di connessione:
E/flutter ( 1234): ❌ Network error - impossible to reach backend

# Verifica:
1. Backend Python è in esecuzione?
2. Porta 8000 è corretta?
3. Firewall non blocca la porta?
4. IP config è corretta (10.0.2.2 vs 192.168.x.x)?
```

### Scenario 2: Analisi Manuale (Premium)

**Test:**
```
1. Vai a Home → "Analizza Manualmente"
2. Compila form:
   - Nome Prodotto: "Biscotti al Cioccolato"
   - Ingredienti: "acqua, zucchero, farina, burro, cacao, lievito"
   - Categoria: "food"
   - Lingua: "it"
3. Clicca "Analizza"
4. ✅ Vedi risultati con score
   → SUCCESS!
```

### Scenario 3: Allergie Personalizzate

**Test:**
```
1. Vai a Impostazioni
2. Aggiungi allergia: "Glutine"
3. Aggiungi allergia: "Latte"
4. Torna a home e scansiona un prodotto con glutine/latte
5. ✅ Badge allergene evidenziato rosso
   → SUCCESS!
```

### Scenario 4: Storico Scansioni

**Test:**
```
1. Scansiona 3-4 prodotti diversi
2. Vai a Storico
3. ✅ Vedi lista di scansioni con:
   - Score card con colore
   - Nome prodotto
   - Data/ora ("Oggi alle 14:30", "Ieri", etc.)
4. Clicca su uno → naviga a dettagli prodotto
   → SUCCESS!
```

### Scenario 5: Premium Toggle

**Test:**
```
1. Vai a Impostazioni
2. Toggle "Account Premium" ON
3. Torna a home
4. "Analizza Manualmente" ora è accessibile
5. ✅ Feature premium abilitate
   → SUCCESS!
```

---

## 📱 Testing su Device Fisico - Checklist

### Android Device

- [ ] USB Debugging abilitato
- [ ] Device riconosciuto: `adb devices`
- [ ] Permessi USB concessi on-device
- [ ] Firewall consente porta 8000
- [ ] Backend raggiungibile: `http://YOUR_IP:8000/health`
- [ ] IP in `api_client.dart` è corretto
- [ ] App installa correttamente: `flutter run`
- [ ] Camera funziona (permessi concessi)
- [ ] Scansione barcode funziona
- [ ] Network call va a backend (log: `📦 Fetching...`)

### iOS Device

- [ ] Xcode installato: `xcode-select --install`
- [ ] Team ID configurato
- [ ] Provisioning profile valido
- [ ] Device trusted (Trust Developer)
- [ ] Firewall consente porta 8000
- [ ] Backend raggiungibile: `http://YOUR_IP:8000/health`
- [ ] IP in `api_client.dart` è corretto
- [ ] Build per device: `flutter run -d <device_id>`

---

## 🐛 Troubleshooting

### "Impossibile raggiungere il server"

```bash
# Verifica 1: Backend è in esecuzione?
curl http://localhost:8000/health
# Deve ritornare: {"status":"ok"}

# Verifica 2: Porta aperta?
netstat -ano | findstr :8000
# Deve mostrare processo in ascolto

# Verifica 3: IP config corretta?
# Android emulator:  10.0.2.2:8000
# iOS simulator:     127.0.0.1:8000
# Device fisico:     192.168.x.x:8000

# Verifica 4: Firewall?
# Windows Firewall: Aggiungi eccezione per porta 8000
netsh advfirewall firewall add rule name="Allow 8000" dir=in action=allow protocol=tcp localport=8000
```

### "Prodotto non trovato nel database"

```bash
# Popola il database con seed:
cd c:\Projects\wye\backend
python .\scripts\seed_db.py

# Verifica dati nel DB:
# Connetti a PostgreSQL
psql -U postgres -d wye
SELECT * FROM products LIMIT 5;
```

### "JSON parse error"

```bash
# Il backend ritorna JSON malformato
# Debug: vai a backend, stampa il response

# Nel backend Python (app/main.py):
@app.get("/product/{barcode}")
async def get_product(barcode: str):
    product = db.query_product_by_barcode(barcode)
    print(f"DEBUG: Returning {product.to_json()}")  # Aggiungi debug
    return product.to_json()
```

### "Camera permission denied"

**Android:**
```
Settings → App Permissions → WYE → Camera → Allow
```

**iOS:**
```
Settings → WYE → Camera → Allow
```

### "App crashes on startup"

```bash
# Leggi i log:
flutter run -v  # Verbose logging

# Verifica dipendenze:
flutter pub get
flutter pub upgrade

# Pulisci e rebuild:
flutter clean
flutter pub get
flutter run
```

---

## 🔍 Logging e Debug

### Abilita Verbose Logging
```bash
flutter run -v
```

Vedrai output come:
```
I/flutter (12345): 📦 Fetching product for barcode: 8718206112001
D/flutter (12345): Response status: 200
D/flutter (12345): Response body: {"barcode": "8718206112001", ...}
I/flutter (12345): ✅ Product found: Nutella
```

### Visualizza Log in tempo reale
```bash
# In un terminale separato
flutter logs
```

### Breakpoints Debugging
```bash
# Avvia con debugger
flutter run

# Nel terminal flutter, premi:
# 'v' = visualizza albero widget
# 'p' = performance info
# 't' = test all events
# 'L' = layout boundaries
```

---

## 📊 Checklist Finale Testing

Prima di commitare il codice:

- [ ] App avvia senza crash
- [ ] Backend connessione funziona
- [ ] Barcode scan (manual input) funziona
- [ ] Manuale analysis form funziona
- [ ] Storico scansioni salva dati
- [ ] Allergie personalizzate funzionano
- [ ] Premium toggle funziona
- [ ] UI responsive su device diversi
- [ ] Camera permission richiesta e gestita
- [ ] Error messages chiari all'utente
- [ ] Logs sono leggibili e utili
- [ ] Nessun uncaught exception
- [ ] Hot reload funziona
- [ ] Build release compila senza errori

---

## 🚀 Prossimi Step dopo MVP Testing

1. **Implementare mobile_scanner vero** (ora è placeholder)
2. **Aggiungere Hive local cache** (offline mode)
3. **Firebase Analytics** per tracking
4. **Sentry error reporting** per production
5. **Unit tests** per logic critica
6. **Integration tests** per user flows

---

## 📞 Tips & Tricks

### Hot Reload vs Hot Restart
```bash
# Durante 'flutter run', premi:
# 'r' = Hot Reload (veloce, mantiene state)
# 'R' = Hot Restart (ricrea app, pulisce state)
```

### Cancellare cache locale
```dart
// Nel SettingsScreen aggiungere un bottone:
ElevatedButton.icon(
  onPressed: () {
    DatabaseService().clearAll();
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Cache cancellata')),
    );
  },
  icon: const Icon(Icons.delete),
  label: const Text('Cancella Cache'),
)
```

### Mock Backend per Testing
```dart
// Per testare senza backend Python:
class MockApiClient extends ApiClient {
  @override
  Future<Product> getProductByBarcode(String barcode) async {
    await Future.delayed(const Duration(milliseconds: 500));
    return Product(
      barcode: barcode,
      productName: 'Test Product',
      brand: 'Test Brand',
      category: 'food',
      ingredientScore: 45,
      nutritionScore: 75,
      finalScore: 55,
      riskLevel: 'moderate',
      ingredients: ['water', 'sugar'],
      allergens: [],
    );
  }
}
```

---

Buon testing! 🎉
