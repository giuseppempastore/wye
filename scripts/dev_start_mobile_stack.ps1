[CmdletBinding()]
param(
    [string]$EvidenceDir = ''
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$composeFile = Join-Path $projectRoot 'compose.mobile.yaml'
$localRoot = Join-Path $projectRoot '.local'
$envFile = Join-Path $localRoot 'mobile-stack.env'
$evidenceRoot = Join-Path $projectRoot 'test_evidence'
$env:DOCKER_CONFIG = Join-Path $localRoot 'docker-config'

function Find-DockerCommand {
    $command = Get-Command docker -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $candidates = @(
        'C:\Program Files\Docker\Docker\resources\bin\docker.exe',
        (Join-Path $env:LOCALAPPDATA 'Programs\Docker Desktop\resources\bin\docker.exe')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    throw 'Docker CLI non trovato. Completa l installazione di Docker Desktop.'
}

function Start-DockerDesktopIfNeeded {
    param([string]$DockerCommand)
    & $DockerCommand info *> $null
    if ($LASTEXITCODE -eq 0) { return }

    $desktopCandidates = @(
        'C:\Program Files\Docker\Docker\Docker Desktop.exe',
        (Join-Path $env:LOCALAPPDATA 'Programs\Docker Desktop\Docker Desktop.exe')
    )
    $desktop = $desktopCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $desktop) { throw 'Docker Desktop non trovato.' }

    Write-Host 'Avvio Docker Desktop...'
    Start-Process -FilePath $desktop -WindowStyle Hidden | Out-Null
    for ($attempt = 1; $attempt -le 90; $attempt++) {
        Start-Sleep -Seconds 2
        & $DockerCommand info *> $null
        if ($LASTEXITCODE -eq 0) { return }
    }
    throw 'Docker Desktop non e diventato disponibile entro 3 minuti.'
}

function Get-PrivateHostIp {
    $addresses = Get-NetIPConfiguration |
        Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq 'Up' } |
        ForEach-Object { $_.IPv4Address.IPAddress } |
        Where-Object { $_ -and $_ -notlike '169.254.*' -and $_ -ne '127.0.0.1' }
    $address = $addresses | Select-Object -First 1
    if (-not $address) { throw 'Nessun indirizzo IPv4 LAN utilizzabile trovato.' }
    return $address
}

function Read-LocalEnvironment {
    param([string]$Path)
    $values = @{}
    if (Test-Path -LiteralPath $Path) {
        foreach ($line in Get-Content -LiteralPath $Path) {
            if (-not $line -or $line.TrimStart().StartsWith('#')) { continue }
            $parts = $line.Split('=', 2)
            if ($parts.Count -eq 2) { $values[$parts[0]] = $parts[1] }
        }
    }
    return $values
}

function Write-LocalEnvironment {
    param([hashtable]$Values, [string]$Path)
    $orderedNames = @(
        'WYE_MOBILE_HOST_IP',
        'WYE_POSTGRES_USER',
        'WYE_POSTGRES_PASSWORD',
        'WYE_POSTGRES_DB',
        'WYE_MINIO_ROOT_USER',
        'WYE_MINIO_ROOT_PASSWORD',
        'WYE_STORAGE_BUCKET',
        'WYE_IMAGE_API_KEY'
    )
    $lines = foreach ($name in $orderedNames) { "$name=$($Values[$name])" }
    Set-Content -LiteralPath $Path -Value $lines -Encoding ASCII
}

New-Item -ItemType Directory -Force -Path $localRoot,$evidenceRoot,$env:DOCKER_CONFIG | Out-Null
if (-not $EvidenceDir) {
    $runId = 'phase9_stack_' + (Get-Date -Format 'yyyyMMdd_HHmmss')
    $EvidenceDir = Join-Path $evidenceRoot $runId
}
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
Set-Content -LiteralPath (Join-Path $evidenceRoot 'LATEST_PHASE9.txt') -Value $EvidenceDir -Encoding ASCII

$hostIp = Get-PrivateHostIp
$values = Read-LocalEnvironment -Path $envFile
$values['WYE_MOBILE_HOST_IP'] = $hostIp
if (-not $values['WYE_POSTGRES_USER']) { $values['WYE_POSTGRES_USER'] = 'wye_mobile' }
if (-not $values['WYE_POSTGRES_PASSWORD']) { $values['WYE_POSTGRES_PASSWORD'] = [guid]::NewGuid().ToString('N') }
if (-not $values['WYE_POSTGRES_DB']) { $values['WYE_POSTGRES_DB'] = 'wye' }
if (-not $values['WYE_MINIO_ROOT_USER']) { $values['WYE_MINIO_ROOT_USER'] = 'wye' + [guid]::NewGuid().ToString('N').Substring(0,12) }
if (-not $values['WYE_MINIO_ROOT_PASSWORD']) { $values['WYE_MINIO_ROOT_PASSWORD'] = ([guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')) }
if (-not $values['WYE_STORAGE_BUCKET']) { $values['WYE_STORAGE_BUCKET'] = 'wye-mobile-local' }
if (-not $values['WYE_IMAGE_API_KEY']) { $values['WYE_IMAGE_API_KEY'] = ([guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')) }
Write-LocalEnvironment -Values $values -Path $envFile

$docker = Find-DockerCommand
Start-DockerDesktopIfNeeded -DockerCommand $docker

$upLog = Join-Path $EvidenceDir 'compose-up.log'
$upStdout = Join-Path $EvidenceDir 'compose-up.stdout.tmp'
$upStderr = Join-Path $EvidenceDir 'compose-up.stderr.tmp'
Write-Host 'Avvio PostgreSQL, MinIO e FastAPI...'
$composeProcess = Start-Process -FilePath $docker -ArgumentList @(
    'compose','--env-file',$envFile,'-f',$composeFile,
    'up','-d','--build','--remove-orphans'
) -RedirectStandardOutput $upStdout -RedirectStandardError $upStderr -Wait -PassThru -WindowStyle Hidden
$composeOutput = @()
if (Test-Path -LiteralPath $upStdout) { $composeOutput += Get-Content -LiteralPath $upStdout }
if (Test-Path -LiteralPath $upStderr) { $composeOutput += Get-Content -LiteralPath $upStderr }
Set-Content -LiteralPath $upLog -Value $composeOutput -Encoding UTF8
Remove-Item -LiteralPath $upStdout,$upStderr -Force -ErrorAction SilentlyContinue
$composeExitCode = $composeProcess.ExitCode
if ($composeExitCode -ne 0) { throw "docker compose up fallito. Vedi $upLog" }

$healthy = $false
for ($attempt = 1; $attempt -le 60; $attempt++) {
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2
        if ($health.status -eq 'ok') { $healthy = $true; break }
    }
    catch { Start-Sleep -Seconds 2 }
}
if (-not $healthy) {
    & $docker compose --env-file $envFile -f $composeFile logs --no-color --timestamps |
        Set-Content -LiteralPath (Join-Path $EvidenceDir 'compose-error.log') -Encoding UTF8
    throw 'FastAPI non e diventato healthy entro 2 minuti.'
}

$fixture = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/product/9876543210987' -TimeoutSec 5
$productId = $fixture.product.id
if (-not $productId) { throw 'Fixture mobile non disponibile.' }

& $docker compose --env-file $envFile -f $composeFile ps --all |
    Set-Content -LiteralPath (Join-Path $EvidenceDir 'compose-ps.txt') -Encoding UTF8
Set-Content -LiteralPath (Join-Path $EvidenceDir 'stack-info.txt') -Encoding ASCII -Value @(
    "host_ip=$hostIp"
    'backend_pc=http://127.0.0.1:8000'
    "backend_phone=http://${hostIp}:8000"
    'backend_emulator=http://10.0.2.2:8000'
    "minio_s3=http://${hostIp}:9000"
    'minio_console=http://127.0.0.1:9001'
    "fixture_barcode=9876543210987"
    "fixture_product_id=$productId"
    'mobile_facade=true_local_e2e_only'
)

Write-Host ''
Write-Host 'STACK MOBILE PRONTO' -ForegroundColor Green
Write-Host 'Health PC:       http://127.0.0.1:8000/health'
Write-Host "Health telefono: http://${hostIp}:8000/health"
Write-Host 'API emulatore:   http://10.0.2.2:8000'
Write-Host "API telefono:    http://${hostIp}:8000"
Write-Host "MinIO S3:        http://${hostIp}:9000"
Write-Host 'MinIO console:   http://127.0.0.1:9001'
Write-Host "Fixture:         barcode 9876543210987, Product ID $productId"
Write-Host "Log sessione:    $EvidenceDir"
