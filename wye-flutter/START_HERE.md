# ⚡ PRIMA DI INIZIARE - Copia e Incolla Questi Commands

## ⚠️ PRE-REQUISITI

Prima di iniziare, assicurati di avere:

- [ ] **Flutter** installato e nel PATH (se no, leggi [FLUTTER_INSTALL.md](FLUTTER_INSTALL.md))
- [ ] **Python 3.8+** installato
- [ ] **Android Emulator** (o device fisico)

Se vedi errore `flutter : Termine 'flutter' non riconosciuto`, vai a [FLUTTER_INSTALL.md](FLUTTER_INSTALL.md) ⬅️

---

## 🎯 Setup in 10 minuti

Copia e incolla questi comandi nei terminal PowerShell.

---

## Terminal 1️⃣: Avvia Backend Python

```powershell
# Vai alla cartella backend
cd c:\Projects\wye\backend

# Attiva venv (se non fatto)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Installa dipendenze
pip install -r requirements.txt

# Popola database
python .\scripts\seed_db.py

# Avvia server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Aspetta finché non vedi:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Terminal 2️⃣: Verifica Backend

```powershell
# In un nuovo terminal, verifica che backend risponde
curl http://localhost:8000/health

# Dovrebbe tornare:
# {"status":"ok"}
```

---

## Terminal 3️⃣: Avvia Android Emulator

```powershell
# Elenca emulator disponibili
flutter emulators

# Avvia uno (sostituisci il nome)
flutter emulators --launch Pixel_4_API_30
```

**Aspetta 30-60 secondi finché Android bootstrap completato.**

---

## Terminal 4️⃣: Avvia Flutter App

```powershell
# Vai alla cartella Flutter
cd c:\Projects\wye\wye-flutter

# Installa dipendenze (prima volta)
flutter pub get

# Avvia app
flutter run

# Aspetta 2-3 minuti per build...
```

**Quando vedi:**
```
Flutter run key commands.
r Hot reload. 🔥🔥🔥
R Hot restart.
h Show help.
w List all attached devices.
q Quit (terminate the app on use 'flutter run').
```

**✅ APP È AVVIATA!**

---

## 🎮 Test in App (Subito!)

Nel emulator/device, fai click:

1. **Home Screen** (dovrebbe essere auto)
2. Clicca **"Scansiona Barcode"**
3. Inserisci: `8718206112001` (Nutella)
4. Clicca **"Cerca Prodotto"**

### Risultato Atteso:
```
✅ Vedi schermata con:
   - Score: 42/100 (rosso/arancio)
   - Ingredient Score: 32
   - Nutrition Score: 65
   - Allergens: Nocciole, Latte, Soia
   - Lista ingredienti

🎉 SUCCESS! Backend connesso e funziona!
```

### Se vedi "Prodotto non trovato":
```powershell
# Popola di nuovo il database
cd c:\Projects\wye\backend
python .\scripts\seed_db.py

# E riprova in app
```

---

## 🧪 Test Veloce (2 minuti)

### Test 1: Scansione
```
Home → Scansiona → 8718206112001 → Vedi risultati ✅
```

### Test 2: Analisi Manuale
```
Home → Analizza Manualmente → Riempi form → Analizza → Vedi risultati ✅
```

### Test 3: Storico
```
(Dopo 2-3 scansioni) → Storico → Vedi lista ✅
```

### Test 4: Allergie
```
Impostazioni → Allergie → Aggiungi "Glutine" → Salva ✅
```

---

## 🆘 Se Qualcosa Non Funziona

### "Impossibile raggiungere il server"
```powershell
# Verifica che backend è in esecuzione
curl http://localhost:8000/health

# Se non risponde, ripeti Terminal 1
```

### "Prodotto non trovato"
```powershell
# Verifica che database è popolato
cd c:\Projects\wye\backend
python .\scripts\seed_db.py
```

### "App crashes"
```powershell
# In Terminal 4, premi Ctrl+C
# Poi:
flutter clean
flutter pub get
flutter run
```

### "Emulator non si avvia"
```powershell
# Usa Android Studio: 
# Tools → Device Manager → Click Play su un emulator
```

---

## 🎯 Prossimi Step

Dopo che tutto funziona:

1. **Leggi QUICK_START.md** - Setup completo
2. **Leggi TESTING_GUIDE.md** - Test scenarios dettagliati
3. **Leggi ARCHITECTURE.md** - Come è strutturato il codice
4. **Commit su git** - Salva il lavoro

---

## 📊 Logs Utili

Nel Terminal 4 (dove è in esecuzione `flutter run`), dovresti vedere:

```
I/flutter (12345): 📦 Fetching product for barcode: 8718206112001
D/flutter (12345): Response status: 200
I/flutter (12345): ✅ Product found: Nutella
```

Se vedi questi log = **Tutto funziona! ✅**

---

## 💡 Pro Tips

### Hot Reload (Modifica codice velocemente)
Durante `flutter run`, premi **`r`** per reload senza riavviare.

### Hot Restart
Premi **`R`** per restart completo (mantiene device).

### Vedi Widget Tree
Durante `flutter run`, premi **`v`** per visualizzare la struttura UI.

### Esci da Flutter
Durante `flutter run`, premi **`q`** per uscire.

---

## ✅ Checklist Finale

Prima di dire "funziona!":

- [ ] Terminal 1: Backend è in esecuzione (vedi "Uvicorn running")
- [ ] Terminal 2: `curl http://localhost:8000/health` ritorna OK
- [ ] Terminal 3: Emulator è avviato (vedi Android home)
- [ ] Terminal 4: App è in esecuzione (vedi Flutter welcome)
- [ ] Puoi inserire barcode e ricevere risultati
- [ ] Storico scansioni funziona
- [ ] Allergie si salvano

**Se tutto ✅ = Pronto per usare l'app! 🎉**

---

## 📞 Se Hai Domande

1. Guarda i log in Terminal 4
2. Leggi TESTING_GUIDE.md Troubleshooting section
3. Verifica che backend è raggiungibile
4. Prova con MockApiClient (no backend needed)

---

**Buon testing! 🚀**
