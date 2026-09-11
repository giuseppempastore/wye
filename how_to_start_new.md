# Test Phase 9 sul telefono: un solo comando

Lo stack locale usa Docker Compose:

```text
Flutter sul telefono
        |
        v
FastAPI in Docker :8000
        |------------------|
        v                  v
PostgreSQL             MinIO/S3 :9000
```

Python e le dipendenze del backend sono dentro il container. Non devi attivare
virtualenv, eseguire `pip` o lanciare `uvicorn` manualmente.

## Quello che devi fare

1. Collega e sblocca il telefono `UGX4Q8CIOFKNFMX4`.
2. Assicurati che `Debug USB` sia attivo.
3. Apri PowerShell ed esegui:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Projects\wye\start_phase9_test.ps1
```
Test sul telefono lasciando acceso il server
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Projects\wye\start_phase9_test.ps1 -Target phone -KeepServerRunning

Avviare soltanto il server
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Projects\wye\scripts\dev_start_mobile_stack.ps1

Spegnere il server
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Projects\wye\stop_phase9_stack.ps1


AVVIO PIXEL_7
"C:\Android\Sdk\emulator\emulator.exe" -avd Pixel_7 -camera-back webcam1 -camera-front webcam1 -no-snapshot-load

test su PIXEL_7
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Projects\wye\start_phase9_test.ps1 -Target emulator -KeepServerRunning

Lo script:

- avvia automaticamente Docker Desktop se necessario;
- attende fino a tre minuti che il motore Docker sia davvero pronto;
- avvia PostgreSQL, MinIO e FastAPI;
- applica le migrazioni al database;
- crea una fixture locale di test;
- prepara automaticamente la connessione tecnica in memoria;
- compila e apre Flutter sul device;
- registra tutti i log nella cartella della sessione.

Non devi aprire Docker Desktop manualmente. Se Docker richiede un intervento
straordinario (per esempio aggiornare WSL o accettare una schermata iniziale),
lo script lo segnala con un messaggio comprensibile e salva lo stato in
`docker-startup.txt`, senza sostituire l'errore principale con errori secondari.

Il terminale mostra il `Product ID` della fixture. Non devi copiare, incollare o
configurare credenziali nell'app.

Quando hai finito premi `q` nel terminale. Lo script salva il risultato e ferma
lo stack, salvo uso di `-KeepServerRunning`.

## Log automatici

Ogni test crea una cartella distinta:

```text
C:\Projects\wye\test_evidence\phase9_DATA_ORA_UGX4Q8CIOFKNFMX4
```

Per chiedere una diagnosi non incollare i log. Scrivi soltanto:

```text
esamina l'ultima sessione Phase 9
```

`test_evidence\LATEST_PHASE9.txt` indica quale cartella deve essere esaminata.

## Avviare soltanto backend, database e MinIO

Se non vuoi aprire Flutter:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Projects\wye\scripts\dev_start_mobile_stack.ps1
```

Indirizzi stampati dallo script:

- health sul PC: `http://127.0.0.1:8000/health`;
- API emulatore Android: `http://10.0.2.2:8000`;
- API telefono fisico: `http://IP_DEL_PC:8000`;
- MinIO/S3 dal telefono: `http://IP_DEL_PC:9000`;
- console MinIO solo PC: `http://127.0.0.1:9001`.

Per fermare lo stack avviato separatamente:

```powershell
$env:DOCKER_CONFIG='C:\Projects\wye\.local\docker-config'; & 'C:\Program Files\Docker\Docker\resources\bin\docker.exe' compose --env-file C:\Projects\wye\.local\mobile-stack.env -f C:\Projects\wye\compose.mobile.yaml down
```

## Sicurezza locale

Le credenziali casuali sono conservate soltanto in
`.local\mobile-stack.env`, ignorato da Git. La facade mobile e abilitata dal
solo file `compose.mobile.yaml` con runtime `e2e`; rimane disabilitata per
default negli altri ambienti.

## Se l'emulatore dice “Lost connection to device”

Questo messaggio non significa automaticamente che il server sia caduto.
Controlla prima `android-exit-info-sanitized.txt` nella cartella della sessione.

La sessione `phase9_20260907_205950_Pixel_7` è terminata perché l'emulatore
esponeva zero fotocamere (`Available cameras: 0`): CameraX ha chiuso il processo
Android, mentre FastAPI/PostgreSQL/MinIO erano ancora attivi e healthy.

La UI ora intercetta questa configurazione prima di avviare CameraX e mostra
“Fotocamera non disponibile” senza chiudere l'app. Per scansionare davvero un
barcode nell'emulatore devi comunque configurare una camera virtuale:

1. Chiudi l'emulatore.
2. Android Studio → Device Manager → matita sul Pixel 7.
3. `Show Advanced Settings` → `Camera`.
4. Imposta almeno `Back` su `VirtualScene` oppure `Webcam0`.
5. Salva, riavvia l'AVD e rilancia `start_phase9_test.ps1` scegliendo emulatore.

Se non vuoi configurare la camera virtuale, usa il telefono fisico: la
registrazione mantiene il barcode scanner-only e non inventa un inserimento
manuale.
