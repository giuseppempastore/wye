[CmdletBinding()]
param(
    [ValidateSet('phone', 'emulator')]
    [string]$Target = 'phone',
    [string]$DeviceId = '',
    [string]$AvdName = 'Pixel_7',
    [switch]$KeepServerRunning
)

$ErrorActionPreference = 'Stop'
$projectRoot = 'C:\Projects\wye'
$flutterRoot = Join-Path $projectRoot 'wye-flutter'
$composeFile = Join-Path $projectRoot 'compose.mobile.yaml'
$envFile = Join-Path $projectRoot '.local\mobile-stack.env'
$stackScript = Join-Path $projectRoot 'scripts\dev_start_mobile_stack.ps1'
$flutterPath = 'C:\flutter\bin\flutter.bat'
$adbPath = 'C:\Android\Sdk\platform-tools\adb.exe'
$emulatorPath = 'C:\Android\Sdk\emulator\emulator.exe'
$defaultPhoneDeviceId = 'UGX4Q8CIOFKNFMX4'
if (-not $DeviceId -and $Target -eq 'phone') { $DeviceId = $defaultPhoneDeviceId }
$runTargetLabel = if ($Target -eq 'emulator') { $AvdName } else { $DeviceId }
$testRunId = 'phase9_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + $runTargetLabel
$evidenceRoot = Join-Path $projectRoot 'test_evidence'
$evidenceDir = Join-Path $evidenceRoot $testRunId
$launcherLog = Join-Path $evidenceDir 'launcher.log'
$flutterLog = Join-Path $evidenceDir 'flutter-private.log'
$feedbackFile = Join-Path $evidenceDir 'ux-feedback.txt'
$env:DOCKER_CONFIG = Join-Path $projectRoot '.local\docker-config'
$docker = $null
$stackStarted = $false
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

function Test-DockerDaemon {
    param([string]$DockerCommand)

    if (-not $DockerCommand) { return $false }
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'SilentlyContinue'
        & $DockerCommand info *> $null
        return ($LASTEXITCODE -eq 0)
    }
    catch {
        return $false
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

function Read-EnvironmentValue {
    param([string]$Name)
    $line = Get-Content -LiteralPath $envFile |
        Where-Object { $_ -like "$Name=*" } |
        Select-Object -First 1
    if (-not $line) { throw "Configurazione $Name assente." }
    return $line.Substring($Name.Length + 1)
}

function Get-ConnectedEmulatorId {
    $line = & $adbPath devices 2>$null |
        Where-Object { $_ -match '^emulator-\d+\s+device$' } |
        Select-Object -First 1
    if (-not $line) { return $null }
    return ($line -split '\s+')[0]
}

function Start-Phase9Emulator {
    if (-not (Test-Path -LiteralPath $emulatorPath)) {
        throw "Android Emulator non trovato: $emulatorPath"
    }

    $phase9AndroidUserHome = $env:ANDROID_USER_HOME
    $env:ANDROID_USER_HOME = Join-Path $env:USERPROFILE '.android'
    try {
        & $adbPath start-server | Out-Null
        $connectedId = Get-ConnectedEmulatorId
        if (-not $connectedId) {
            $availableAvds = @(& $emulatorPath -list-avds)
            if ($AvdName -notin $availableAvds) {
                throw "Emulatore $AvdName non disponibile. Disponibili: $($availableAvds -join ', ')"
            }

            Write-Phase9Message "Avvio emulatore Android $AvdName..."
            Start-Process -FilePath $emulatorPath -ArgumentList @('-avd', $AvdName) | Out-Null

            for ($attempt = 1; $attempt -le 120; $attempt++) {
                Start-Sleep -Seconds 2
                $connectedId = Get-ConnectedEmulatorId
                if ($connectedId) { break }
            }
        }
        if (-not $connectedId) { throw 'Emulatore non collegato entro 4 minuti.' }

        for ($attempt = 1; $attempt -le 90; $attempt++) {
            $bootCompleted = (& $adbPath -s $connectedId shell getprop sys.boot_completed 2>$null | Select-Object -First 1)
            if ($bootCompleted -eq '1') { return $connectedId }
            Start-Sleep -Seconds 2
        }
        throw "Emulatore $connectedId collegato, ma Android non si e avviato entro 3 minuti."
    }
    finally {
        $env:ANDROID_USER_HOME = $phase9AndroidUserHome
    }
}

function Save-AndroidExitEvidence {
    $exitInfoFile = Join-Path $evidenceDir 'android-exit-info-sanitized.txt'
    $deviceState = (& $adbPath get-state 2>$null | Select-Object -First 1)
    if ($deviceState -ne 'device') {
        Set-Content -LiteralPath $exitInfoFile -Encoding ASCII -Value 'device_state=unavailable'
        return
    }

    $safeLines = @()
    $safeLines += & $adbPath shell dumpsys activity exit-info com.example.wye 2>$null |
        Where-Object { $_ -match '(ApplicationExitInfo|timestamp=|reason=|status=|importance=|pss=|rss=|description=|processStateSummary=)' }
    $safeLines += & $adbPath logcat -d -v time AndroidRuntime:E ActivityManager:I lmkd:I '*:S' 2>$null |
        Where-Object { $_ -match '(com\.example\.wye|FATAL EXCEPTION|OutOfMemoryError|low memory|Killing)' }
    $safeLines = $safeLines |
        Select-Object -Last 160 |
        ForEach-Object {
            $_ -replace '\b\d{8,14}\b','<redacted-number>' `
               -replace 'https?://\S+','<redacted-url>' `
               -replace 'UGX[A-Z0-9]+','<redacted-device>'
        }
    if ($safeLines.Count -eq 0) { $safeLines = @('android_exit_evidence=not_available') }
    Set-Content -LiteralPath $exitInfoFile -Encoding UTF8 -Value $safeLines
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
    if ($Target -eq 'emulator') {
        Write-Phase9Message 'Controllo l emulatore...'
        $DeviceId = Start-Phase9Emulator
        Write-Phase9Message "EMULATORE OK: $DeviceId"
    }
    else {
        Write-Phase9Message 'Controllo il telefono...'
        & $adbPath start-server | Out-Null
        $deviceLines = & $adbPath devices
        if (-not ($deviceLines -match ('^' + [regex]::Escape($DeviceId) + '\s+device$'))) {
            throw "Il telefono $DeviceId non e autorizzato. Sbloccalo, accetta Debug USB e rilancia."
        }
        Write-Phase9Message 'TELEFONO OK'
    }

    $failureStage = 'DOCKER_STACK'
    & $stackScript -EvidenceDir $evidenceDir
    $stackStarted = $true
    $docker = Find-DockerCommand
    if (-not $docker) { throw 'Docker CLI non disponibile dopo lo startup.' }
    Write-Phase9Message 'DOCKER STACK OK'

    $hostIp = Read-EnvironmentValue -Name 'WYE_MOBILE_HOST_IP'
    $apiBaseUrl = if ($Target -eq 'emulator') { 'http://10.0.2.2:8000' } else { "http://${hostIp}:8000" }
    $fixtureInfo = Get-Content -LiteralPath (Join-Path $evidenceDir 'stack-info.txt')
    $fixtureProductId = (($fixtureInfo | Where-Object { $_ -like 'fixture_product_id=*' }) -split '=',2)[1]

    $commit = & git -C $projectRoot rev-parse --short HEAD
    Set-Content -LiteralPath (Join-Path $evidenceDir 'session-info.txt') -Encoding ASCII -Value @(
        "test_run_id=$testRunId"
        "device_id=$DeviceId"
        "target=$Target"
        "commit=$commit"
        'runtime=docker_compose_e2e'
        "api_base_url=$apiBaseUrl"
        "fixture_product_id=$fixtureProductId"
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
    Write-Host " WYE STA PER APRIRSI SU: $DeviceId" -ForegroundColor Green
    Write-Host " Product ID di test: $fixtureProductId"
    Write-Host ' Connessione tecnica: automatica e invisibile.'
    Write-Host ' Usa l app e valuta la User Experience.'
    Write-Host ' Quando hai finito torna qui e premi q.'
    Write-Host " Sessione: $testRunId"
    Write-Host '============================================================' -ForegroundColor Green
    Write-Host ''

    $failureStage = 'FLUTTER_PUB_GET'
    Push-Location $flutterRoot
    try {
        # Flutter/Gradle scrive alcuni warning su stderr. In Windows PowerShell 5
        # non devono essere scambiati per eccezioni che interrompono la sessione.
        $ErrorActionPreference = 'Continue'
        & $flutterPath pub get 2>&1 | Tee-Object -FilePath $flutterLog -Append
        if ($LASTEXITCODE -ne 0) { throw "flutter pub get fallito con codice $LASTEXITCODE." }

        $failureStage = 'FLUTTER_RUN'
        & $flutterPath run --no-pub -d $DeviceId '--dart-define=WYE_MOBILE_UPLOAD_ENABLED=true' "--dart-define=API_BASE_URL=$apiBaseUrl" 2>&1 |
            Tee-Object -FilePath $flutterLog -Append
        $flutterExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = 'Stop'
        Pop-Location
    }

    if (Select-String -LiteralPath $flutterLog -SimpleMatch 'Lost connection to device.' -Quiet) {
        $failureStage = 'FLUTTER_DEVICE_CONNECTION'
        throw 'Flutter ha perso il processo sul telefono. Consulta android-exit-info-sanitized.txt.'
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
    if ($failureStage -eq 'FLUTTER_DEVICE_CONNECTION') {
        $failureFeedback = Read-Host 'Descrivi in una riga l ultimo gesto eseguito prima della chiusura'
        if (-not [string]::IsNullOrWhiteSpace($failureFeedback)) {
            Add-Content -LiteralPath $feedbackFile -Value "feedback_operatore=$failureFeedback" -Encoding UTF8
        }
    }
    Write-Host ''
    Write-Host "Scrivimi: esamina l'ultima sessione Phase 9." -ForegroundColor Yellow
}
finally {
    Save-AndroidExitEvidence

    if (-not $docker) { $docker = Find-DockerCommand }
    $dockerDaemonReady = Test-DockerDaemon -DockerCommand $docker
    if ($dockerDaemonReady -and (Test-Path -LiteralPath $envFile)) {
        try {
            $previousErrorActionPreference = $ErrorActionPreference
            $ErrorActionPreference = 'Continue'
            & $docker compose --env-file $envFile -f $composeFile logs --no-color --timestamps 2>$null |
                Set-Content -LiteralPath (Join-Path $evidenceDir 'compose-final.log') -Encoding UTF8
        }
        catch {
            Write-Phase9Message 'Log finali Docker non disponibili; il risultato principale della sessione resta invariato.'
        }
        finally {
            $ErrorActionPreference = $previousErrorActionPreference
        }
        if ($stackStarted -and -not $KeepServerRunning) {
            Write-Host 'Arresto intenzionale dello stack Docker...' -ForegroundColor DarkYellow
            & $docker compose --env-file $envFile -f $composeFile down --remove-orphans | Out-Null
        }
        elseif ($stackStarted) {
            Write-Host 'Server lasciato attivo su http://127.0.0.1:8000' -ForegroundColor Green
            Write-Host 'Per arrestarlo: powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Projects\wye\stop_phase9_stack.ps1'
        }
    }
    elseif ($stackStarted) {
        Write-Phase9Message 'Il motore Docker non e piu disponibile: impossibile raccogliere i log finali o arrestare lo stack.'
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
