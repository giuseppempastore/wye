# 🐦 Installazione Flutter - Windows

## ⚡ Opzione 1: Installazione Veloce (Consigliato)

### Step 1: Download Flutter SDK

1. Vai a https://flutter.dev/docs/get-started/install/windows
2. Clicca il link **"Download Flutter SDK"** (versione Windows)
3. Salva il file ZIP (circa 600 MB)

### Step 2: Estrai in una cartella

Estrai il file ZIP in una cartella **senza spazi nel percorso**:

```
C:\flutter
```

⚠️ **NON** usare percorsi con spazi: `C:\Program Files\flutter` ❌

### Step 3: Aggiungi Flutter al PATH

```powershell
# Apri PowerShell come Administrator (Win+X → Windows Terminal (Admin))

# Aggiungi Flutter al PATH permanentemente
[Environment]::SetEnvironmentVariable("Path", "$env:Path;C:\flutter\bin", "User")

# Chiudi e riapri PowerShell

# Verifica che funziona
flutter --version
```

Se vedi:
```
Flutter 3.x.x • channel ...
```

✅ **Installazione completata!**

---

## ⚡ Opzione 2: Installazione via Chocolatey (Se hai Chocolatey)

```powershell
# Come Administrator
choco install flutter

# Riavvia PowerShell e verifica
flutter --version
```

---

## ⚡ Opzione 3: Usando Android Studio

1. Apri **Android Studio**
2. Vai a **Tools → SDK Manager → SDK Tools**
3. Seleziona **Flutter SDK**
4. Android Studio installa automaticamente e configura PATH

---

## ✅ Dopo l'Installazione

```powershell
# Verifica che tutto è installato
flutter doctor

# Dovrebbe mostrare:
# [✓] Flutter (Channel stable, 3.x.x)
# [✓] Android toolchain
# [✓] Android Studio
# etc.
```

Se tutti gli item hanno `[✓]` = **Pronto! 🎉**

---

## 🆘 Se `flutter --version` non funziona ancora

1. **Chiudi e riapri PowerShell** (completamente)
2. Usa il percorso completo:
   ```powershell
   C:\flutter\bin\flutter --version
   ```
3. Se funziona, il PATH non è stato aggiornato. Ripeti Step 3.

---

## 📝 Dopo che Flutter è Installato

Torna a **START_HERE.md** e riprova:

```powershell
flutter emulators
```

Dovrebbe funzionare! ✅

---

## 💡 Pro Tip: Android Studio + Flutter

Se usi Android Studio, puoi installare il plugin Flutter:

1. **File → Settings → Plugins**
2. Cerca **Flutter**
3. Installa il plugin ufficiale
4. Riavvia Android Studio

Poi puoi lanciare l'emulator da Android Studio:
**Tools → Device Manager → Avvia Emulator**

E poi in terminal:
```powershell
cd c:\Projects\wye\wye-flutter
flutter run
```

---

**Una volta installato, leggi START_HERE.md per il setup! 🚀**
