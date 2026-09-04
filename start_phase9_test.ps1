[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = 'C:\Projects\wye'
$flutterRoot = Join-Path $projectRoot 'wye-flutter'
$composeFile = Join-Path $projectRoot 'compose.mobile.yaml'
$envFile = Join-Path $projectRoot '.local\mobile-stack.env'
$stackScript = Join-Path $projectRoot 'scripts\dev_start_mobile_stack.ps1'
$flutterPath = 'C:\flutter\bin\flutter.bat'
$adbPath = 'C:\Android\Sdk\platform-tools\adb.exe'
$deviceId = 'UGX4Q8CIOFKNFMX4'
$testRunId = 'phase9_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + $deviceId
$evidenceRoot = Join-Path $projectRoot 'test_evidence'
$evidenceDir = Join-Path $evidenceRoot $testRunId
$launcherLog = Join-Path $evidenceDir 'launcher.log'
$flutterLog = Join-Path $evidenceDir 'flutter-private.log'
$feedbackFile = Join-Path $evidenceDir 'ux-feedback.txt'
$env:DOCKER_CONFIG = Join-Path $projectRoot '.local\docker-config'
$docker = $null
$stackStarted = $false
$transcriptStarted = $false
$testOutcome = 'IN_PROGRESS'
$failureStage = 'NONE'

function Write-Phase9Message {
    param([string]$Message)
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $line
    Add-Content -LiteralPath $launcherLog -Value $line -Encoding UTF8
}

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
    return $null
}

function Read-EnvironmentValue {
    param([string]$Name)
    $line = Get-Content -LiteralPath $envFile |
        Where-Object { $_ -like "$Name=*" } |
        Select-Object -First 1
    if (-not $line) { throw "Configurazione $Name assente." }
    return $line.Substring($Name.Length + 1)
}

New-Item -ItemType Directory -Force -Path $evidenceDir,$env:DOCKER_CONFIG | Out-Null
Set-Content -LiteralPath (Join-Path $evidenceRoot 'LATEST_PHASE9.txt') -Value $evidenceDir -Encoding ASCII

try {
    Write-Phase9Message "SESSIONE: $testRunId"
    Write-Phase9Message "LOG: $evidenceDir"

    if (-not (Test-Path -LiteralPath $flutterPath)) { $failureStage = 'FLUTTER_TOOL'; throw "Flutter non trovato: $flutterPath" }
    if (-not (Test-Path -LiteralPath $adbPath)) { $failureStage = 'ADB_TOOL'; throw "ADB non trovato: $adbPath" }

    $env:ANDROID_HOME = 'C:\Android\Sdk'
    $env:ANDROID_SDK_ROOT = 'C:\Android\Sdk'
    $env:ANDROID_USER_HOME = 'C:\wyehome\.android'
    $env:ANDROID_SDK_HOME = 'C:\wyehome'
    $env:JAVA_HOME = 'C:\Program Files\Java\jdk-17'
    $env:GRADLE_USER_HOME = 'C:\wyehome\.gradle'
    $env:PUB_CACHE = 'C:\wyehome\Pub\Cache'
    New-Item -ItemType Directory -Force -Path $env:ANDROID_USER_HOME,$env:GRADLE_USER_HOME,$env:PUB_CACHE | Out-Null

    $failureStage = 'DEVICE'
    Write-Phase9Message 'Controllo il telefono...'
    & $adbPath start-server | Out-Null
    $deviceLines = & $adbPath devices
    if (-not ($deviceLines -match ('^' + [regex]::Escape($deviceId) + '\s+device$'))) {
        throw "Il telefono $deviceId non e autorizzato. Sbloccalo, accetta Debug USB e rilancia."
    }
    Write-Phase9Message 'TELEFONO OK'

    $failureStage = 'DOCKER_STACK'
    $stackStarted = $true
    & $stackScript -EvidenceDir $evidenceDir
    $docker = Find-DockerCommand
    if (-not $docker) { throw 'Docker CLI non disponibile dopo lo startup.' }
    Write-Phase9Message 'DOCKER STACK OK'

    $hostIp = Read-EnvironmentValue -Name 'WYE_MOBILE_HOST_IP'
    $imageApiKey = Read-EnvironmentValue -Name 'WYE_IMAGE_API_KEY'
    $fixtureInfo = Get-Content -LiteralPath (Join-Path $evidenceDir 'stack-info.txt')
    $fixtureProductId = (($fixtureInfo | Where-Object { $_ -like 'fixture_product_id=*' }) -split '=',2)[1]

    $failureStage = 'MOBILE_SESSION'
    $sessionResponse = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/mobile/dev/v1/capture/sessions' -Headers @{'X-WYE-Image-Key'=$imageApiKey} -ContentType 'application/json' -Body '{"scopes":["upload","extraction"]}'
    $sessionResponse.access_token | Set-Clipboard
    $imageApiKey = $null
    $sessionResponse = $null
    Write-Phase9Message 'Token mobile copiato negli appunti (15 minuti).'

    $commit = & git -C $projectRoot rev-parse --short HEAD
    Set-Content -LiteralPath (Join-Path $evidenceDir 'session-info.txt') -Encoding ASCII -Value @(
        "test_run_id=$testRunId"
        "device_id=$deviceId"
        "commit=$commit"
        'runtime=docker_compose_e2e'
        "api_base_url=http://${hostIp}:8000"
        "fixture_product_id=$fixtureProductId"
        'fixture_barcode=9876543210987'
    )
    Set-Content -LiteralPath $feedbackFile -Encoding UTF8 -Value @(
        "test_run_id=$testRunId"
        'result=DA_COMPILARE'
        'cosa_ho_provato='
        'cosa_mi_aspettavo='
        'cosa_e_successo='
        'punto_esatto_del_problema='
    )

    Write-Host ''
    Write-Host '============================================================' -ForegroundColor Green
    Write-Host ' WYE STA PER APRIRSI SUL TELEFONO' -ForegroundColor Green
    Write-Host " Product ID di test: $fixtureProductId"
    Write-Host ' Barcode di test:    9876543210987'
    Write-Host ' Token: gia copiato; incollalo in Settings se serve.'
    Write-Host ' Usa l app e valuta la User Experience.'
    Write-Host ' Quando hai finito torna qui e premi q.'
    Write-Host " Sessione: $testRunId"
    Write-Host '============================================================' -ForegroundColor Green
    Write-Host ''

    $failureStage = 'FLUTTER_PUB_GET'
    Push-Location $flutterRoot
    try {
        Start-Transcript -Path $flutterLog -Append | Out-Null
        $transcriptStarted = $true
        & $flutterPath pub get
        if ($LASTEXITCODE -ne 0) { throw "flutter pub get fallito con codice $LASTEXITCODE." }

        $failureStage = 'FLUTTER_RUN'
        & $flutterPath run --no-pub -d $deviceId '--dart-define=WYE_MOBILE_UPLOAD_ENABLED=true' "--dart-define=API_BASE_URL=http://${hostIp}:8000"
        $flutterExitCode = $LASTEXITCODE
    }
    finally {
        if ($transcriptStarted) {
            Stop-Transcript | Out-Null
            $transcriptStarted = $false
        }
        Pop-Location
    }

    if ($flutterExitCode -ne 0) { throw "Flutter si e chiuso con codice $flutterExitCode." }
    $testOutcome = 'COMPLETED_BY_OPERATOR'
    $failureStage = 'NONE'
    $feedback = Read-Host 'Scrivi in una riga il tuo feedback UX (oppure premi Invio)'
    if (-not [string]::IsNullOrWhiteSpace($feedback)) {
        Add-Content -LiteralPath $feedbackFile -Value "feedback_operatore=$feedback" -Encoding UTF8
    }
}
catch {
    $testOutcome = 'FAILED_OR_BLOCKED'
    Write-Phase9Message "ERRORE nello step $failureStage [$($_.Exception.GetType().Name)]: $($_.Exception.Message)"
    Write-Host ''
    Write-Host "Scrivimi: esamina l'ultima sessione Phase 9." -ForegroundColor Yellow
}
finally {
    if ($transcriptStarted) { Stop-Transcript | Out-Null }
    Set-Clipboard -Value ''

    if (-not $docker) { $docker = Find-DockerCommand }
    if ($docker -and (Test-Path -LiteralPath $envFile)) {
        & $docker compose --env-file $envFile -f $composeFile logs --no-color --timestamps 2>$null |
            Set-Content -LiteralPath (Join-Path $evidenceDir 'compose-final.log') -Encoding UTF8
        if ($stackStarted) {
            & $docker compose --env-file $envFile -f $composeFile down --remove-orphans | Out-Null
        }
    }

    Set-Content -LiteralPath (Join-Path $evidenceDir 'result.txt') -Encoding ASCII -Value @(
        "test_run_id=$testRunId"
        "outcome=$testOutcome"
        "failure_stage=$failureStage"
        "finished_at=$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
        "evidence_dir=$evidenceDir"
    )
    Write-Host ''
    Write-Host "Test terminato. Log: $evidenceDir" -ForegroundColor Cyan
    Write-Host "Per farmeli esaminare: esamina l'ultima sessione Phase 9." -ForegroundColor Cyan
}
