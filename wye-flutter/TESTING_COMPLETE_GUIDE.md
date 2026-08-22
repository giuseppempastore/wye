# 🚀 WYE Flutter App - GUIDA COMPLETA PER TESTING

## ✅ Cosa è stato Implementato

### ✨ MVP Flutter Production-Ready

```
✅ 6 Screen Completi (Home, Scanner, Detail, Manual, History, Settings)
✅ State Management (Provider pattern)
✅ Navigation (Go Router)
✅ API Client (JSON parsing, error handling robusto)
✅ Mobile Scanner Integration (camera barcode)
✅ Local Database (Hive per offline mode)
✅ Theme System (Material Design 3, colori dinamici)
✅ Componenti Riusabili (ScoreCard, RiskTag, AllergenBadge)
✅ Logging Completo (Logger package)
✅ Mock API Client (testing offline)
✅ Documentazione Completa
```

---

## 📋 Checklist Setup Iniziale

Prima di iniziare i test, verifica:

- [ ] Flutter installato: `flutter --version`
- [ ] Android Studio/Xcode installato
- [ ] Emulator disponibile: `flutter emulators`
- [ ] Backend Python clonato: `c:\Projects\wye\backend`
- [ ] PostgreSQL installato e running
- [ ] Git configurato per committare

---

## 🎯 3 MODI PER TESTARE

### Modalità 1️⃣: Testing Online (Consigliato MVP)

**Backend + Emulator + App**

```powershell
# Terminal 1: Backend Python
cd c:\Projects\wye\backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Android Emulator
flutter emulators --launch <emulator_name>

# Terminal 3: Flutter App
cd c:\Projects\wye\wye-flutter
flutter run

# Terminal 4: Verifica Backend
curl http://localhost:8000/health
```

**Risultato**: App connessa a backend, barcode scan funziona.

---

### Modalità 2️⃣: Testing Offline (No Backend)

**Solo MockApiClient**

```dart
// lib/main.dart - Cambia:

// ORIGINALE:
Provider<ApiClient>(create: (_) => ApiClient()),

// MOCK:
Provider<ApiClient>(create: (_) => MockApiClient()),
```

```powershell
cd c:\Projects\wye\wye-flutter
flutter run

# Usa barcode di test:
# - 8718206112001 (Nutella)
# - 5901234123457 (Biscotti)
# - 4006381333931 (Snack)
```

**Vantaggio**: Testa UI/UX senza backend.

---

### Modalità 3️⃣: Testing Device Fisico

**Android Device USB + Backend**

```powershell
# Terminal 1: Backend
cd c:\Projects\wye\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Trova IP locale
ipconfig
# Esempio: 192.168.1.100

# Terminal 3: Aggiorna IP in api_client.dart
# static const String baseUrl = 'http://192.168.1.100:8000';

# Terminal 4: Flutter run on device
flutter run -d <device_id>
```

---

## 📱 STEP BY STEP - First Run

### Step 1: Prepara il Backend
```powershell
cd c:\Projects\wye\backend

# Setup venv (solo prima volta)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Installa dipendenze
pip install -r requirements.txt

# Popola database con seed
python .\scripts\seed_db.py

# Avvia server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Verifica**: `curl http://localhost:8000/health` → `{"status":"ok"}`

### Step 2: Avvia Emulator
```powershell
flutter emulators --launch Pixel_4_API_30
# (o il tuo emulator disponibile)

# Aspetta 30-60 secondi
```

### Step 3: Avvia Flutter App
```powershell
cd c:\Projects\wye\wye-flutter

# Prima volta - installa dipendenze
flutter pub get

# Avvia app
flutter run

# Aspetta 2-3 minuti per il build
```

### Step 4: Testa in App
```
Home Screen → Clicca "Scansiona Barcode"
  ↓
Inserisci barcode: 8718206112001
  ↓
Clicca "Cerca Prodotto"
  ↓
✅ Aspetta risultati dal backend
```

**Risultato Atteso:**
```
Score: 42/100 (rosso)
Ingredienti Score: 32/100
Nutrition Score: 65/100
Allergens: Nocciole, Latte, Soia
```

---

## 🔍 Test Cases Essenziali

### Test 1: Barcode Scan (5 min)
```
✅ Input: 8718206112001
✅ Output: Prodotto Nutella con scores
✅ Allergens mostrati
✅ Storico aggiornato
```

### Test 2: Analisi Manuale (5 min)
```
✅ Input: Prodotto + ingredienti (it)
✅ Output: Scores calcolati
✅ No backend required
✅ Allergens rilevati
```

### Test 3: Allergie Personalizzate (3 min)
```
✅ Aggiungi allergia: "Glutine"
✅ Scansiona prodotto con glutine
✅ Badge allergia evidenziato rosso
```

### Test 4: Storico Scansioni (3 min)
```
✅ Scansiona 3 prodotti
✅ Vai a Storico
✅ Vedi tutti con date formattate
✅ Clicca → naviga a dettagli
```

### Test 5: Premium Toggle (2 min)
```
✅ Vai a Impostazioni
✅ Toggle Premium ON
✅ Torna a home
✅ "Analizza Manualmente" ora accessibile
```

**Total Time**: ~20 minuti per testare tutto.

---

## 🛠️ Configurazione IP Device

| Device | IP | Comando |
|--------|----|---------| 
| **Android Emulator** | `10.0.2.2:8000` | Default |
| **iOS Simulator** | `127.0.0.1:8000` | `ipconfig` → localhost |
| **Android Device** | `192.168.1.X:8000` | `ipconfig` → cerca IPv4 |
| **iOS Device** | `192.168.1.X:8000` | WiFi → Info |

**Cambia in**: `lib/services/api_client.dart`
```dart
class ApiConfig {
  static const String baseUrl = 'http://10.0.2.2:8000';  // Cambia qui
}
```

---

## 📊 Debugging & Logs

### Abilita Verbose Logging
```bash
flutter run -v    # Leggi tutti i log
flutter logs      # In un terminale separato
```

### Vedi i Log Importanti
```
I/flutter: 📦 Fetching product for barcode: 8718206112001
I/flutter: ✅ Product found: Nutella
```

### Debug con Breakpoints
```bash
flutter run

# Nel terminal flutter:
'v' = visualizza widget tree
'p' = performance info
'L' = show layout boundaries
'q' = exit
```

---

## ⚠️ Troubleshooting Veloce

| Problema | Soluzione |
|----------|-----------|
| **Network error** | Backend non running. Avvia: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| **Prodotto non trovato** | DB vuoto. Esegui: `python .\scripts\seed_db.py` |
| **JSON parse error** | Backend ritorna JSON malformato. Aggiorna API. |
| **App crashes** | `flutter clean && flutter pub get && flutter run` |
| **Camera not working** | Concedi permessi in Settings → App Permissions |
| **Emulator not found** | `flutter emulators --launch <name>` o Android Studio |

---

## 📁 File Importanti

```
wye-flutter/
├── QUICK_START.md          ← Inizia da qui! (5 min setup)
├── TESTING_GUIDE.md        ← Guida testing completa
├── ARCHITECTURE.md         ← Design system & flow
├── ENV_CONFIG.md           ← Environment config
├── pubspec.yaml            ← Dipendenze Flutter
│
├── lib/
│   ├── main.dart          ← Entry point + MultiProvider
│   ├── theme/app_theme.dart    ← Colori, tipografia
│   ├── models/product_model.dart   ← Data models
│   ├── services/
│   │   ├── api_client.dart     ← HTTP client (vero)
│   │   ├── mock_api_client.dart ← Mock per testing
│   │   └── database_service.dart   ← Hive caching
│   ├── providers/app_providers.dart  ← State management
│   ├── router/app_router.dart   ← Navigation
│   ├── screens/            ← 6 screen completi
│   └── widgets/score_widgets.dart   ← Componenti UI
│
└── README.md              ← Setup generale
```

---

## 🚀 Deployment Ready?

### Checklist Pre-Release
- [ ] API endpoint funzionanti
- [ ] DB popolato con seed data
- [ ] Barcode scan funziona su device
- [ ] Allergie salvataggio locale OK
- [ ] Storico funziona
- [ ] No uncaught exceptions
- [ ] Build APK/IPA senza errori
- [ ] App testing su Play Store Console

### Build Release
```bash
# Android APK
flutter build apk --release

# iOS IPA
flutter build ios --release
```

---

## 📚 Documentazione Disponibile

1. **QUICK_START.md** ← Inizia qui (5 min)
2. **TESTING_GUIDE.md** ← Test completo (20 min)
3. **ARCHITECTURE.md** ← Design deep dive
4. **ENV_CONFIG.md** ← Configuration
5. **README.md** ← Setup generale

---

## 🎯 Prossimi Step

### Fase 2 (Dopo MVP Testing)
- [ ] Aggiungere unit tests
- [ ] Integration tests per user flows
- [ ] Firebase Analytics
- [ ] Sentry error reporting
- [ ] Push notifications

### Fase 3 (Before Release)
- [ ] Localization (it, en, fr, es)
- [ ] Offline mode completo con Hive
- [ ] App signing & certificate
- [ ] Privacy policy & Terms
- [ ] Play Store & App Store submission

---

## 💬 Support

Se hai problemi:

1. **Leggi TESTING_GUIDE.md** - Troubleshooting section
2. **Abilita verbose logging**: `flutter run -v`
3. **Controlla logs**: Backend e Flutter logs
4. **Verifica connessione**: `curl http://localhost:8000/health`
5. **Usa MockApiClient**: Testa offline

---

## 🎉 Success Criteria

✅ Quando vedi tutto funzionare:

- App avvia senza crash
- Scansione barcode ritorna risultati
- Storico salva scansioni
- Allergie personalizzate funzionano
- Premium toggle funziona
- UI responsive su device diversi
- Backend connessione stabile

**Se tutto funziona → Pronto per MVP Release!**

---

## 📞 Quick Reference

```bash
# Backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Android Emulator
flutter emulators --launch <name>

# Flutter App
cd wye-flutter && flutter run

# Logs
flutter logs

# Clean
flutter clean && flutter pub get

# Build Release
flutter build apk --release

# Test
flutter run -v
```

---

Buon testing! 🚀 Dimmi se hai domande!
