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

1. Avvia Docker Desktop, se non e gia aperto.
2. Collega e sblocca il telefono `UGX4Q8CIOFKNFMX4`.
3. Assicurati che `Debug USB` sia attivo.
4. Apri PowerShell ed esegui:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Projects\wye\start_phase9_test.ps1
```

Lo script:

- avvia automaticamente Docker Desktop se necessario;
- avvia PostgreSQL, MinIO e FastAPI;
- applica le migrazioni al database;
- crea una fixture con barcode `9876543210987`;
- crea una sessione mobile e copia il token negli appunti;
- compila e apre Flutter sul device;
- registra tutti i log nella cartella della sessione.

Il terminale mostra il `Product ID` della fixture. Per provare l'upload, apri
Settings nell'app e incolla il token gia presente negli appunti.

Quando hai finito premi `q` nel terminale. Lo script salva il risultato, ferma
lo stack e pulisce il token dagli appunti.

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
