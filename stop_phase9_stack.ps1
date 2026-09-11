[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = 'C:\Projects\wye'
$composeFile = Join-Path $projectRoot 'compose.mobile.yaml'
$envFile = Join-Path $projectRoot '.local\mobile-stack.env'
$env:DOCKER_CONFIG = Join-Path $projectRoot '.local\docker-config'

if (-not (Test-Path -LiteralPath $envFile)) {
    throw "Configurazione locale non trovata: $envFile"
}

$dockerCommand = Get-Command docker -ErrorAction SilentlyContinue
$docker = if ($dockerCommand) {
    $dockerCommand.Source
}
else {
    'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
}

if (-not (Test-Path -LiteralPath $docker)) {
    throw 'Docker CLI non trovato.'
}

Write-Host 'Arresto PostgreSQL, MinIO, FastAPI e acquisition worker...'
& $docker compose --env-file $envFile -f $composeFile down --remove-orphans
if ($LASTEXITCODE -ne 0) { throw "Arresto Docker fallito con codice $LASTEXITCODE." }
Write-Host 'Stack Phase 9 arrestato. I volumi dati sono stati conservati.' -ForegroundColor Green
