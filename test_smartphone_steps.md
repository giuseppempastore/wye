# 📱 Guida al Setup & Avvio dell'Ambiente di Sviluppo
> **Backend Python + Flutter su Dispositivo Fisico Android**

Questa guida documenta la procedura completa per configurare l'ambiente di sviluppo, risolvere i problemi relativi ai percorsi di sistema su Windows (es. caratteri speciali/accentati come `Giuseppeù`) e avviare il backend Python in combinazione con l'app Flutter in esecuzione su un dispositivo fisico Android via USB.

---

## 🛠️ 1. Configurazione Una Tantum del Sistema
Esegui questi passaggi la prima volta per configurare correttamente l'ambiente, bypassando i problemi di percorsi utente di Windows ed esponendo `adb` a livello globale.

### Step 1.1: Reset della configurazione di Flutter
Apri **PowerShell** ed elimina eventuali riferimenti a vecchi percorsi dell'SDK errati:
```powershell
flutter config --android-sdk ""
```

### Step 1.2: Installazione di Platform-Tools in una cartella pulita
Crea la cartella `C:\WinGet\platform-tools` (priva di caratteri speciali) ed estrai l'SDK ufficiale di Google:
```powershell
# Scarica lo zip dei platform-tools
Invoke-WebRequest -Uri "https://dl.google.com/android/repository/platform-tools-latest-windows.zip" -OutFile "$env:TEMP\platform-tools.zip"

# Estrai il contenuto in C:\WinGet
Expand-Archive -Path "$env:TEMP\platform-tools.zip" -DestinationPath "C:\WinGet" -Force
```

### Step 1.3: Aggiunta di ADB alle Variabili d'Ambiente (PATH)
Aggiungi in modo permanente il percorso `C:\WinGet\platform-tools` alle variabili d'ambiente dell'utente:
```powershell
[System.Environment]::SetEnvironmentVariable("Path", [System.Environment]::GetEnvironmentVariable("Path", "User") + ";C:\WinGet\platform-tools", "User")
```

> ⚠️ **Importante:** Dopo aver eseguito questo comando, **chiudi e riapri completamente VS Code** (o la tua finestra del terminale) per ricaricare le nuove variabili d'ambiente.

---

## 🔌 2. Configurazione Hardware del Telefono (Popup RSA)
Collega lo smartphone al computer tramite cavo USB e sblocca lo schermo.

1. **Imposta la connessione USB:**
   * Trascina verso il basso la tendina delle notifiche sul telefono.
   * Seleziona **Sistema Android • Ricarica USB**.
   * Cambia la modalità in **Trasferimento di file / MTP**.

2. **Abilita il Debug USB (Opzioni Sviluppatore):**
   * Vai su `Impostazioni > Opzioni sviluppatore`.
   * Clicca su **Revoca autorizzazioni debug USB** e conferma premendo **OK**.
   * Disattiva e riattiva l'interruttore **Debug USB**.

3. **Inizializza la connessione sicura:**
   * Esegui i seguenti comandi dal terminale di VS Code per riavviare il demone ADB e forzare la comparsa del popup di sicurezza:
     ```powershell
     adb kill-server
     adb devices
     ```
   * Guarda subito lo schermo del telefono: spunta la casella **"Consenti sempre da questo computer"** nel popup dell'autorizzazione RSA e seleziona **Consenti**.

---

## 🚀 3. Procedura di Avvio Quotidiana
Per avviare l'intero ecosistema di sviluppo, apri due terminali separati in VS Code.

### 🎛️ Terminale 1: Avvio Backend Python (Uvicorn)
Avvia il server backend FastAPI/Uvicorn sulla porta `8000`:
```powershell
Start-Process -FilePath 'C:\Projects\wye\.venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','app.main:app','--app-dir','C:\Projects\wye\backend','--host','0.0.0.0','--port','8000' -WorkingDirectory 'C:\Projects\wye\backend'
```

### 📱 Terminale 2: Inoltro Porte (ADB Reverse) & Avvio Flutter
1. **Verifica lo stato del dispositivo:**
   ```powershell
   adb devices
   ```
   *Assicurati che il tuo dispositivo (es. `UGX4Q8CIOFKNFMX4`) sia elencato como `device` e **non** come `unauthorized`.*

2. **Inoltra il traffico (Reverse Proxy USB):**
   ```powershell
   adb reverse tcp:8000 tcp:8000
   ```
   > 💡 **Nota:** Questo comando reindirizza tutte le chiamate effettuate dall'app a `http://127.0.0.1:8000` direttamente alla porta `8000` del tuo PC tramite cavo USB.

3. **Spostati nella cartella del progetto Flutter:**
   ```powershell
   cd wye-flutter
   ```

4. **Verifica il riconoscimento da parte di Flutter:**
   ```powershell
   flutter devices
   ```

5. **Avvia l'applicazione Flutter:**
   ```powershell
   flutter run -d UGX4Q8CIOFKNFMX4 --dart-define=API_BASE_URL=http://127.0.0.1:8000
   ```

> ⚠️ **Se compare il prompt di Windows:** `Terminare il processo batch (S/N)?`  
> Rispondi **`N`** (No). Se rispondi **`S`**, il processo di installazione di Gradle/Android SDK viene interrotto e la build si blocca.

> 💡 Se `flutter run` mostra che mancano i pacchetti Android, esegui:
> ```powershell
> Remove-Item "C:\Android\Sdk\.temp" -Recurse -Force -ErrorAction SilentlyContinue
> & "C:\Android\Sdk\cmdline-tools\latest\bin\sdkmanager.bat" --sdk_root="C:\Android\Sdk" --install "platform-tools" "platforms;android-36" "build-tools;36.0.0" "ndk;28.2.13676358"
> ```

---

## 🔍 4. Risoluzione Rapida dei Problemi

| Problema | Causa Comune | Soluzione |
| :--- | :--- | :--- |
| **Stato `unauthorized` con `adb devices`** | Mancata autorizzazione RSA sul telefono | Esegui `adb kill-server`, scollega e ricollega il cavo USB, sblocca lo schermo e accetta il popup di autorizzazione sul telefono. |
| **Prompt `Terminare il processo batch (S/N)?`** | Gradle/SDK install viene interrotto accidentalmente | Rispondi **`N`** (No). Se hai selezionato **`S`**, riavvia la build e, se necessario, cancella `C:\Android\Sdk\.temp` prima di reinstallare i pacchetti Android. |
| **`permission_handler_android requires Android SDK 37` / `compileSdk = 37`** | Plugin richiesto da Android 37 + progetto configurato con SDK più basso | Imposta `compileSdk = 37` in `android/app/build.gradle.kts` e installa i pacchetti `platforms;android-37` e `build-tools;37.0.0`. |
| **Errore Java 26 / Gradle/AGP incompatibile** | JDK troppo nuovo rispetto alla toolchain Android | Usa Java 17 (o 21 se supportato dal tuo toolchain) e imposta `JAVA_HOME` correttamente; evita JDK 26 per questa build. |
| **`FileSystemException` / `Path not found` in Flutter** | Presenza di caratteri speciali (es. lettere accentate) nel path dell'SDK di Flutter o di Android | Esegui il comando `flutter config --android-sdk ""` ed assicurati che `adb` sia installato ed eseguito dal percorso pulito `C:\WinGet\platform-tools`. |

---

## ✅ Checklist giornaliera per testare l'app senza creare un nuovo profilo utente

Questa checklist usa sempre lo stesso ambiente stabile e fa sì che non serva ricreare un nuovo profilo utente Windows. Il segreto è usare sempre un `HOME` ASCII e un `JAVA_HOME` corretto.

### 1) Apri un terminale PowerShell nuovo
```powershell
$env:USERPROFILE = 'C:\wyehome'
$env:HOME = 'C:\wyehome'
$env:ANDROID_HOME = 'C:\Android\Sdk'
$env:ANDROID_SDK_ROOT = 'C:\Android\Sdk'
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-17'
$env:GRADLE_USER_HOME = 'C:\wyehome\.gradle'
$env:PUB_CACHE = 'C:\wyehome\Pub\Cache'
$env:KOTLIN_DAEMON_JVM_ARGS = '-Duser.home=C:\wyehome'

New-Item -ItemType Directory -Force -Path $env:GRADLE_USER_HOME, $env:PUB_CACHE | Out-Null
```

### 2) Se ci sono daemon di Gradle/Kotlin vecchi, li interrompi
```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.Name -match 'java' -and $_.CommandLine -match 'gradle|kotlin|GradleDaemon|KotlinCompileDaemon' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
```

### 3) Verifica che il telefono sia autorizzato
```powershell
adb kill-server
adb devices
```

Se appare `unauthorized`, scollega e ricollega il cavo, sblocca il telefono e accetta il popup RSA.

### 4) Avvia il backend
```powershell
Start-Process -FilePath 'C:\Projects\wye\.venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','app.main:app','--app-dir','C:\Projects\wye\backend','--host','0.0.0.0','--port','8000' -WorkingDirectory 'C:\Projects\wye\backend'
```

### 5) Fai il reverse port verso il telefono
```powershell
adb reverse tcp:8000 tcp:8000
```

### 6) Entra nel progetto Flutter
```powershell
cd C:\Projects\wye\wye-flutter
```

### 7) Verifica il device e avvia l'app
```powershell
flutter devices
flutter run -d UGX4Q8CIOFKNFMX4 --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

### 8) Controlli finali
- Sul telefono compare l'app
- Compila senza rimanere in `Running Gradle task 'assembleDebug'...`
- La app riesce a chiamare il backend su `127.0.0.1:8000`
- `adb devices` mostra il dispositivo come `device`

---

### ⚠️ Se l'app si blocca di nuovo
Esegui solo questi due passaggi:
```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.Name -match 'java' -and $_.CommandLine -match 'gradle|kotlin' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

$env:USERPROFILE = 'C:\wyehome'
$env:HOME = 'C:\wyehome'
$env:ANDROID_HOME = 'C:\Android\Sdk'
$env:ANDROID_SDK_ROOT = 'C:\Android\Sdk'
$env:JAVA_HOME = 'C:\Program Files\Java\jdk-17'
$env:GRADLE_USER_HOME = 'C:\wyehome\.gradle'
$env:PUB_CACHE = 'C:\wyehome\Pub\Cache'

cd C:\Projects\wye\wye-flutter
flutter clean
flutter pub get
flutter run -d UGX4Q8CIOFKNFMX4 --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

> Questa è la procedura che evita di ricreare un nuovo profilo utente e mantiene un ambiente Windows stabile per i test quotidiani. |
