# Avvio e test locale (Windows)

Questa guida spiega passo-passo i comandi per avviare il backend, seedare il database e diagnosticare i problemi più comuni su Windows.

## 1) Permettere temporaneamente l'esecuzione di script in questa sessione
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

Spiegazione: PowerShell per sicurezza blocca l'esecuzione di script non firmati. `RemoteSigned` permette gli script locali non firmati ma richiede la firma per script scaricati da Internet. `-Scope Process` applica la policy solo alla sessione corrente (quando chiudi la finestra la policy torna quella precedente).

## 2) Verificare il `python` del virtualenv
& 'C:\Projects\wye\.venv\Scripts\python.exe' -V

Spiegazione: conferma che il virtualenv esiste e che userai l'interprete corretto. Useremo sempre questo `python.exe` per installare pacchetti e avviare il server.

## 3) Aggiornare pip / setuptools / wheel e installare le dipendenze
& 'C:\Projects\wye\.venv\Scripts\python.exe' -m pip install --upgrade pip setuptools wheel
& 'C:\Projects\wye\.venv\Scripts\python.exe' -m pip install -r C:\Projects\wye\backend\requirements.txt

Spiegazione: aggiorna gli strumenti di packaging e installa le dipendenze del progetto (FastAPI, Uvicorn, psycopg2-binary, ecc.). Assicurati di eseguire questi comandi con lo stesso `python.exe` del venv.

## 4) Risolvere problemi con `psycopg2` (compilazione C)
& 'C:\Projects\wye\.venv\Scripts\python.exe' -m pip uninstall -y psycopg2 psycopg2-binary
& 'C:\Projects\wye\.venv\Scripts\python.exe' -m pip install psycopg2-binary
& 'C:\Projects\wye\.venv\Scripts\python.exe' -m pip show psycopg2-binary

Spiegazione: `psycopg2` ha componenti in C; se pip non trova una ruota compatibile tenta di compilare e richiede i Visual C++ Build Tools. `psycopg2-binary` fornisce una ruota precompilata per la maggior parte delle piattaforme e evita la compilazione.

## 5) Eseguire il seed del database
& 'C:\Projects\wye\.venv\Scripts\python.exe' C:\Projects\wye\backend\scripts\seed_db.py

Spiegazione: lo script applica i file SQL in `postgres/seeds/` per inserire ingredienti, allergeni e prodotti di esempio nel DB `wye`. Lo script usa le variabili d'ambiente (`PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`) o `postgres/user_postgres.txt` per le credenziali.

## 6) Avviare il server (foreground)
& 'C:\Projects\wye\.venv\Scripts\python.exe' -m uvicorn app.main:app --app-dir 'C:\Projects\wye\backend' --reload --host 127.0.0.1 --port 8000

Spiegazione: avvia Uvicorn con l'app `app.main:app`. `--app-dir` specifica la directory dove risiede il package `app` quando esegui il comando da un'altra cartella. `--reload` abilita il reload automatico in sviluppo.

## 7) Aprire una nuova finestra PowerShell che rimane aperta (opzione alternativa)
Start-Process -FilePath powershell -ArgumentList -NoExit, '-Command', "& 'C:\Projects\wye\.venv\Scripts\python.exe' -m uvicorn app.main:app --app-dir 'C:\Projects\wye\backend' --reload --host 127.0.0.1 --port 8000" -WorkingDirectory 'C:\Projects\wye\backend'

Spiegazione: utile se vuoi avviare il server in una finestra separata che non si chiude automaticamente (consente di leggere i log senza perdere la shell corrente).

## 8) Avviare in background e reindirizzare output/errore su file
Start-Process -FilePath 'C:\Projects\wye\.venv\Scripts\python.exe' `
  -ArgumentList '-m','uvicorn','app.main:app','--app-dir','C:\Projects\wye\backend','--reload','--host','127.0.0.1','--port','8000' `
  -WorkingDirectory 'C:\Projects\wye\backend' `
  -RedirectStandardOutput 'C:\Projects\wye\backend\uvicorn.out.txt' `
  -RedirectStandardError  'C:\Projects\wye\backend\uvicorn.err.txt'

Spiegazione: esegue Uvicorn in background come processo separato e salva stdout/stderr su file per analisi successiva.

## 9) Testare rapidamente gli endpoint (dopo l’avvio)
Invoke-RestMethod 'http://127.0.0.1:8000/health'
Invoke-RestMethod 'http://127.0.0.1:8000/product/9876543210987' | ConvertTo-Json -Depth 5

Spiegazione: richieste rapide per verificare che il server risponda e che il prodotto di seed sia raggiungibile.

## 10) (Opzionale) Attivare il virtualenv con `Activate.ps1`
cd C:\Projects\wye
& .\.venv\Scripts\Activate.ps1

Spiegazione: l'attivazione modifica la shell corrente in modo da usare `python` e `pip` del venv senza specificare il percorso completo; richiede la possibilità di eseguire script (vedi punto 1).

## Nota di sicurezza
Non modificare permanentemente la policy di esecuzione a livello di sistema (`LocalMachine`) a meno che tu non sappia cosa stai facendo. `-Scope Process` è temporaneo e sicuro per sviluppo.

*** End Patch