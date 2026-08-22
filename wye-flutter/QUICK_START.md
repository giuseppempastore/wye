# QUICK START - WYE Flutter Testing

## ⚡ Setup in 5 minuti

### 1️⃣ Avvia Backend Python

```powershell
# Terminal 1
cd c:\Projects\wye\backend

# Se è la prima volta
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Avvia il server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Verifica:**
```powershell
# Terminal 2 - testa che backend risponde
curl http://localhost:8000/health
```

Dovrebbe tornare:
```json
{"status":"ok"}
```

### 2️⃣ Avvia Android Emulator

```powershell
# Terminal 3
flutter emulators --launch <emulator_name>

# Oppure manualmente: Android Studio → Device Manager → Play
```

### 3️⃣ Avvia Flutter App

```powershell
# Terminal 4
cd c:\Projects\wye\wye-flutter
flutter run
```

Aspetta che compili... (primo run ~2-3 minuti)

### 4️⃣ Test Scansione

**In-App:**
1. Clicca **"Scansiona Barcode"**
2. Inserisci barcode: `8718206112001` (Nutella)
3. Clicca **"Cerca Prodotto"**

**Risultato atteso:**
```
✅ Se vedi schermata con:
   - Score: 42/100
   - Ingredienti Rischiosi
   - Allergeni (Nocciole)
   → SUCCESS!

❌ Se vedi "Prodotto non trovato":
   → Popola DB: python .\scripts\seed_db.py
```

---

## 📱 Teste Rapidi (2-3 minuti)

### Test 1: Barcode Scansione
```
Home → Scansiona → Input: 8718206112001 → ✅ Vedi risultati
```

### Test 2: Analisi Manuale
```
Home → Analizza Manualmente → Compila → Analizza → ✅ Vedi risultati
```

### Test 3: Storico
```
(Dopo 2-3 scansioni) → Storico → ✅ Vedi lista scansioni
```

### Test 4: Allergie
```
Impostazioni → Allergie → Aggiungi "Glutine" → ✅ Toggle saved
```

---

## 🔧 Configurazione IP per Device Diversi

### Android Emulator ✅
```dart
// lib/services/api_client.dart
static const String baseUrl = 'http://10.0.2.2:8000';
```

### iOS Simulator
```dart
static const String baseUrl = 'http://127.0.0.1:8000';
```

### Device Fisico (Android)
```powershell
# Trova il tuo IP locale
ipconfig
# Cerca "IPv4 Address" nella sezione WiFi (es: 192.168.1.100)
```

```dart
static const String baseUrl = 'http://192.168.1.100:8000';
```

---

## 🐛 Errori Comuni & Soluzioni

| Errore | Soluzione |
|--------|----------|
| "Impossibile raggiungere il server" | Backend non è in esecuzione. Avvia: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| "Prodotto non trovato" | DB vuoto. Esegui: `python .\scripts\seed_db.py` |
| App crashes | Pulisci: `flutter clean && flutter pub get && flutter run` |
| JSON parse error | Backend ritorna JSON malformato. Controlla `app/main.py` |
| Camera permission denied | Concedi permessi in Settings → App Permissions → Camera |

---

## 📊 Prodotti di Test (Seed DB)

Dopo eseguire `seed_db.py`, puoi testare con:

```
8718206112001  → Nutella (reale)
5901234123457  → Test Product 1
4006381333931  → Test Product 2
```

---

## 🔥 Commands Utili

```bash
# Pulisci e rebuild
flutter clean && flutter pub get && flutter run

# Verbose logging
flutter run -v

# Hot reload (durante run)
premi 'r'

# Hot restart (durante run)
premi 'R'

# Logs in tempo reale
flutter logs

# List devices
flutter devices
```

---

## ✅ Quando tutto funziona:

- [ ] Backend Python in esecuzione su port 8000
- [ ] `curl http://localhost:8000/health` ritorna `{"status":"ok"}`
- [ ] Emulator Android avviato
- [ ] App Flutter avviata: `flutter run`
- [ ] Puoi inserire barcode e ricevere risultati dal backend
- [ ] Storico e allergie funzionano

---

## 📝 Prossimi Step

1. **Local caching** con Hive (offline mode)
2. **Mobile scanner** camera integration
3. **OCR** per photo upload
4. **Unit tests** per logic critica

Divertiti! 🚀
