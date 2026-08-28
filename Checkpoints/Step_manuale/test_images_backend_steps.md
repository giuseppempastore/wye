Certo. Ti lascio un **manuale breve e operativo** per testare da backend sia una foto ingredienti sia una tabella nutrizionale.

# Manuale rapido test backend WYE

## 1. Avvia MinIO

In una PowerShell:

```powershell
$env:MINIO_ROOT_USER = "wyeadmin"
$env:MINIO_ROOT_PASSWORD = "wyeadmin123"

C:\Tools\minio\minio.exe server C:\minio-data --console-address ":9001"
```

Verifica:

```powershell
Test-NetConnection localhost -Port 9000
```

Deve risultare:

```text
TcpTestSucceeded : True
```

---

## 2. Configura le variabili runtime

In una seconda PowerShell:

```powershell
cd C:\Projects\wye\backend
```

Database di test:

```powershell
$env:PGHOST = "localhost"
$env:PGPORT = "5432"
$env:PGUSER = "postgres"
$env:PGDATABASE = "wye_e2e"
```

Se serve:

```powershell
$env:PGPASSWORD = "LA_TUA_PASSWORD"
```

Storage:

```powershell
$env:WYE_STORAGE_PROVIDER = "minio"
$env:WYE_STORAGE_ENDPOINT = "http://localhost:9000"
$env:WYE_STORAGE_BUCKET = "wye-private"
$env:WYE_STORAGE_REGION = "us-east-1"
$env:WYE_STORAGE_ACCESS_KEY = "wyeadmin"
$env:WYE_STORAGE_SECRET_KEY = "wyeadmin123"
$env:WYE_STORAGE_FORCE_PATH_STYLE = "true"
```

API WYE:

```powershell
$env:WYE_IMAGE_API_KEY = "wye-local-test"
```

OpenAI:

```powershell
$env:WYE_OPENAI_API_KEY = $env:WYE_OPENAI_KEY
$env:WYE_EXTRACTION_PROVIDER = "openai"
$env:WYE_OPENAI_EXTRACTION_MODEL = "gpt-4o-mini"
$env:WYE_EXTRACTION_TIMEOUT_SECONDS = "90"
```

---

## 3. Verifica migration

```powershell
& 'C:\Projects\wye\backend\venv\Scripts\python.exe' -m alembic upgrade head
```

Poi:

```powershell
& 'C:\Projects\wye\backend\venv\Scripts\python.exe' -m alembic current
```

Deve risultare:

```text
0005_label_extraction_pipeline (head)
```

---

## 4. Avvia FastAPI

```powershell
& 'C:\Projects\wye\backend\venv\Scripts\python.exe' `
  -m uvicorn app.main:app `
  --host 127.0.0.1 `
  --port 8000
```

Lascia la finestra aperta.

In una terza PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Risultato:

```text
status = ok
```

---

# Test foto ingredienti

## 5. Imposta prodotto e immagine

Esempio:

```powershell
$productId = 1
$imagePath = "C:\Projects\wye\test_images\ingredients.jpg"
```

Calcola size e SHA:

```powershell
$size = (Get-Item $imagePath).Length
$sha = (Get-FileHash $imagePath -Algorithm SHA256).Hash.ToLower()
```

---

## 6. Inizializza upload ingredients

```powershell
$headers = @{
    "X-Wye-Image-Key" = "wye-local-test"
}
```

```powershell
$body = @{
    image_type = "ingredients"
    mime_type  = "image/jpeg"
    byte_size  = $size
    sha256     = $sha
} | ConvertTo-Json
```

```powershell
$upload = Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/products/$productId/images/uploads" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $body
```

Controlla:

```powershell
$upload | ConvertTo-Json -Depth 10
```

---

## 7. Carica l'immagine su MinIO

```powershell
Invoke-WebRequest `
    -Method Put `
    -Uri $upload.upload_url `
    -Headers @{ "Content-Type" = "image/jpeg" } `
    -InFile $imagePath
```

---

## 8. Finalizza upload

```powershell
$finalized = Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/products/$productId/images/uploads/$($upload.upload_id)/finalize" `
    -Headers $headers
```

```powershell
$finalized | ConvertTo-Json -Depth 10
```

Imposta:

```powershell
$imageId = $finalized.product_image_id
```

---

## 9. Lancia estrazione ingredienti

```powershell
$idempotencyKey = [guid]::NewGuid().ToString()
```

```powershell
$extractHeaders = @{
    "X-Wye-Image-Key" = "wye-local-test"
    "Idempotency-Key" = $idempotencyKey
}
```

```powershell
$extraction = Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/products/$productId/images/$imageId/extractions" `
    -Headers $extractHeaders `
    -ContentType "application/json" `
    -Body "{}"
```

Visualizza:

```powershell
$extraction | ConvertTo-Json -Depth 15
```

Controlla soprattutto:

```text
run_status = succeeded
provider = openai
items = ingredient_list / ingredient / allergen
```

---

# Test tabella nutrizionale

## 10. Imposta immagine nutrition

```powershell
$nutritionPath = "C:\Projects\wye\test_images\nutrition.jpg"
```

```powershell
$nutritionSize = (Get-Item $nutritionPath).Length
$nutritionSha = (Get-FileHash $nutritionPath -Algorithm SHA256).Hash.ToLower()
```

---

## 11. Inizializza upload nutrition

```powershell
$nutritionBody = @{
    image_type = "nutrition"
    mime_type  = "image/jpeg"
    byte_size  = $nutritionSize
    sha256     = $nutritionSha
} | ConvertTo-Json
```

```powershell
$nutritionUpload = Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/products/$productId/images/uploads" `
    -Headers $headers `
    -ContentType "application/json" `
    -Body $nutritionBody
```

---

## 12. Carica la tabella su MinIO

```powershell
Invoke-WebRequest `
    -Method Put `
    -Uri $nutritionUpload.upload_url `
    -Headers @{ "Content-Type" = "image/jpeg" } `
    -InFile $nutritionPath
```

---

## 13. Finalizza

```powershell
$nutritionFinalized = Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/products/$productId/images/uploads/$($nutritionUpload.upload_id)/finalize" `
    -Headers $headers
```

```powershell
$nutritionImageId = $nutritionFinalized.product_image_id
```

---

## 14. Lancia estrazione nutrition

```powershell
$nutritionIdempotencyKey = [guid]::NewGuid().ToString()
```

```powershell
$nutritionExtractHeaders = @{
    "X-Wye-Image-Key" = "wye-local-test"
    "Idempotency-Key" = $nutritionIdempotencyKey
}
```

```powershell
$nutritionExtraction = Invoke-RestMethod `
    -Method Post `
    -Uri "http://127.0.0.1:8000/products/$productId/images/$nutritionImageId/extractions" `
    -Headers $nutritionExtractHeaders `
    -ContentType "application/json" `
    -Body "{}"
```

Visualizza:

```powershell
$nutritionExtraction | ConvertTo-Json -Depth 15
```

Controlla:

```text
run_status = succeeded
item_type = nutrition
basis = per_100_g / per_serving
```

---

## 15. Regola importante

Ogni nuovo tentativo di extraction deve avere una nuova:

```powershell
[guid]::NewGuid().ToString()
```

come `Idempotency-Key`.

Altrimenti WYE può restituire il run precedente.

---

## Sequenza minima da ricordare

```text
MinIO
→ variabili ambiente
→ Alembic
→ FastAPI
→ image size + SHA
→ initialize upload
→ PUT MinIO
→ finalize
→ nuova Idempotency-Key
→ POST extraction
→ controlla succeeded
```

Se vuoi, posso anche trasformare questo manuale in un file `TEST_BACKEND_IMAGES.md` da tenere direttamente nella repository.
