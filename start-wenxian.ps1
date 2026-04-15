$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$localProjectName = 'literature-screening-local'
$devProjectName = 'literature-screening-dev'

function Ensure-DockerOnPath {
  if (Get-Command docker -ErrorAction SilentlyContinue) { return }

  $candidateDirs = @(
    (Join-Path $env:ProgramFiles 'Docker\Docker\resources\bin'),
    (Join-Path ${env:ProgramFiles(x86)} 'Docker\Docker\resources\bin'),
    (Join-Path $env:LocalAppData 'Programs\Docker\Docker\resources\bin')
  ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

  foreach ($dir in $candidateDirs) {
    $dockerExe = Join-Path $dir 'docker.exe'
    if (Test-Path -LiteralPath $dockerExe) {
      $env:PATH = ($dir + ';' + $env:PATH)
      break
    }
  }

  if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'docker not found. Please install Docker Desktop first (or add Docker to PATH).'
  }
}

function Import-DotEnvFile {
  param([Parameter(Mandatory = $true)][string]$Path)

  if (!(Test-Path -LiteralPath $Path)) { return }

  Get-Content -LiteralPath $Path -ErrorAction Stop | ForEach-Object {
    $line = $_
    if ($null -eq $line) { return }
    $trimmed = $line.Trim()
    if ($trimmed.Length -eq 0) { return }
    if ($trimmed.StartsWith('#')) { return }

    if ($trimmed -match '^\s*export\s+') {
      $trimmed = ($trimmed -replace '^\s*export\s+', '')
    }

    $match = [regex]::Match($trimmed, '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$')
    if (!$match.Success) { return }

    $key = $match.Groups[1].Value
    $value = $match.Groups[2].Value

    if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
      if ($value.Length -ge 2) { $value = $value.Substring(1, $value.Length - 2) }
    }

    [Environment]::SetEnvironmentVariable($key, $value, 'Process')
  }
}

function Stop-LegacyStacks {
  try { & docker compose -f docker-compose.local.yml down *> $null } catch {}
  try { & docker compose -f docker-compose.dev.yml down *> $null } catch {}
}

function Ensure-DockerReady {
  Ensure-DockerOnPath
  $lastOutput = $null
  for ($i = 1; $i -le 60; $i++) {
    $lastOutput = (& cmd /c "docker info 2>&1")
    if ($LASTEXITCODE -eq 0) { return }
    Start-Sleep -Seconds 2
  }

  $message = 'Docker CLI cannot connect to the engine. Docker Desktop may still be starting.'
  if ($lastOutput -match 'Access is denied') {
    $message = $message + ' It looks like a permission issue (Access is denied). Add your Windows user to the "docker-users" group and sign out/in.'
  }
  if ($lastOutput) {
    $message = $message + "`n--- docker info ---`n" + ($lastOutput | Out-String)
  }
  throw $message
}

function Test-TcpPortAvailable {
  param([Parameter(Mandatory = $true)][int]$Port)

  $listener = $null
  try {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
    $listener.Start()
    return $true
  } catch {
    return $false
  } finally {
    if ($listener) {
      try { $listener.Stop() } catch {}
    }
  }
}

function Get-PortDebugHint {
  param([Parameter(Mandatory = $true)][int]$Port)

  try {
    $lines = (& cmd /c "netstat -ano | findstr :$Port") 2>$null
    if (-not $lines) { return $null }
    return ($lines | Out-String)
  } catch {
    return $null
  }
}

function Ensure-OrPickFreePort {
  param(
    [Parameter(Mandatory = $true)][string]$EnvVarName,
    [Parameter(Mandatory = $true)][int]$DefaultPort,
    [Parameter(Mandatory = $true)][int[]]$FallbackPorts
  )

  $existing = [Environment]::GetEnvironmentVariable($EnvVarName, 'Process')
  $explicit = [bool]$existing
  if (-not $existing) {
    $existing = [string]$DefaultPort
    [Environment]::SetEnvironmentVariable($EnvVarName, $existing, 'Process')
  }

  $port = 0
  if (-not [int]::TryParse($existing, [ref]$port)) {
    throw ($EnvVarName + ' must be an integer. Current value: ' + $existing)
  }

  if (Test-TcpPortAvailable -Port $port) { return }

  if ($explicit) {
    $hint = Get-PortDebugHint -Port $port
    $msg = ($EnvVarName + ' port is already in use: ' + $port)
    if ($hint) { $msg = $msg + "`n--- netstat ---`n" + $hint }
    throw $msg
  }

  foreach ($candidate in $FallbackPorts) {
    if (Test-TcpPortAvailable -Port $candidate) {
      [Environment]::SetEnvironmentVariable($EnvVarName, [string]$candidate, 'Process')
      Write-Host ($EnvVarName + ' ' + $port + ' is busy, using ' + $candidate)
      return
    }
  }

  throw ($EnvVarName + ' default port is busy and no fallback port is available.')
}

function Get-RunningComposeServices {
  param(
    [Parameter(Mandatory = $true)][string]$ProjectName,
    [Parameter(Mandatory = $true)][string]$ComposeFile
  )

  $out = (& docker compose -p $ProjectName -f $ComposeFile ps --services --status running 2>&1)
  if ($LASTEXITCODE -ne 0) { return @() }
  return @($out | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

function Wait-ForComposeServicesRunning {
  param(
    [Parameter(Mandatory = $true)][string]$ProjectName,
    [Parameter(Mandatory = $true)][string]$ComposeFile,
    [Parameter(Mandatory = $true)][string[]]$Services,
    [int]$Attempts = 60
  )

  for ($i = 1; $i -le $Attempts; $i++) {
    $running = Get-RunningComposeServices -ProjectName $ProjectName -ComposeFile $ComposeFile
    $missing = @($Services | Where-Object { $running -notcontains $_ })
    if ($missing.Count -eq 0) { return }
    Start-Sleep -Seconds 2
  }

  $runningFinal = Get-RunningComposeServices -ProjectName $ProjectName -ComposeFile $ComposeFile
  throw ('Compose services not running: ' + ($Services -join ', ') + '. Running: ' + ($runningFinal -join ', ') + ". Check: docker compose -p `"$ProjectName`" -f `"$ComposeFile`" ps")
}

function Test-HttpOk {
  param([Parameter(Mandatory = $true)][string]$Url)

  try {
    if ($PSVersionTable.PSVersion.Major -lt 6) {
      Invoke-WebRequest -UseBasicParsing -Uri $Url -Method Get -TimeoutSec 2 | Out-Null
    } else {
      Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 2 | Out-Null
    }
    return $true
  } catch {
    return $false
  }
}

function Wait-ForUrl {
  param(
    [Parameter(Mandatory = $true)][string]$Url,
    [Parameter(Mandatory = $true)][string]$Name,
    [int]$Attempts = 60
  )

  for ($i = 1; $i -le $Attempts; $i++) {
    if (Test-HttpOk -Url $Url) {
      Write-Host ($Name + ' ready: ' + $Url)
      return
    }
    Start-Sleep -Seconds 2
  }

  throw ($Name + ' startup timed out. Run: cd "' + $scriptDir + '" ; docker compose -p "' + $localProjectName + '" -f docker-compose.local.yml logs --tail=100')
}

function Copy-DataIfMissing {
  param(
    [Parameter(Mandatory = $true)][string]$SourceDir,
    [Parameter(Mandatory = $true)][string]$TargetDir
  )

  $targetMarker = Join-Path $TargetDir 'api_runs\projects'
  if (Test-Path -LiteralPath $targetMarker) { return }
  if (!(Test-Path -LiteralPath $SourceDir)) { return }

  New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
  & robocopy $SourceDir $TargetDir /E /R:2 /W:1 /COPY:DAT /DCOPY:DAT /XD __pycache__ .pytest_cache | Out-Null
  $code = $LASTEXITCODE
  if ($code -gt 7) { throw ('Data migration failed: robocopy exit code ' + $code) }
}

Ensure-DockerReady

Import-DotEnvFile -Path (Join-Path $scriptDir '.env')
Import-DotEnvFile -Path (Join-Path $scriptDir 'literature_screening\.env')

if ($env:MOONSHOT_API_KEY -and -not $env:KIMI_API_KEY) {
  $env:KIMI_API_KEY = $env:MOONSHOT_API_KEY
}

if (-not $env:APP_DATA_DIR) {
  $env:APP_DATA_DIR = (Join-Path $scriptDir 'literature_screening\data\api_runs')
}
Ensure-OrPickFreePort -EnvVarName 'API_PORT' -DefaultPort 8000 -FallbackPorts @(8000, 8001, 18000, 28000)
Ensure-OrPickFreePort -EnvVarName 'WEB_PORT' -DefaultPort 8080 -FallbackPorts @(8080, 8081, 8082, 18080, 28080)

New-Item -ItemType Directory -Force -Path $env:APP_DATA_DIR | Out-Null

if (!(Test-Path -LiteralPath (Join-Path $scriptDir 'literature_screening\.env'))) {
  Copy-Item -Force -LiteralPath (Join-Path $scriptDir 'literature_screening\.env.example') -Destination (Join-Path $scriptDir 'literature_screening\.env')
  Write-Host 'Created literature_screening/.env (fill in API keys if needed).'
}

if (-not $env:KIMI_API_KEY -and -not $env:DEEPSEEK_API_KEY) {
  Write-Host 'Note: no KIMI_API_KEY / DEEPSEEK_API_KEY found. The app can start, but creating new AI tasks requires an API key.'
}

# If the new repo does not have data yet, try migrating from sibling old repo (default name: wenxian)
$maybeOldRoot = Resolve-Path (Join-Path $scriptDir '..\wenxian') -ErrorAction SilentlyContinue
if ($maybeOldRoot) {
  Copy-DataIfMissing -SourceDir (Join-Path $maybeOldRoot 'literature_screening\data') -TargetDir (Join-Path $scriptDir 'literature_screening\data')
}

Write-Host 'Starting (local / stable mode)...'
Write-Host ('APP_DATA_DIR: ' + $env:APP_DATA_DIR)
Write-Host ('Web: http://127.0.0.1:' + $env:WEB_PORT)
Write-Host ('API health: http://127.0.0.1:' + $env:API_PORT + '/api/health')

Stop-LegacyStacks
try { & docker compose -p $devProjectName -f docker-compose.dev.yml down *> $null } catch {}

& docker compose -p $localProjectName -f docker-compose.local.yml up -d --build

if ($LASTEXITCODE -ne 0) {
  $hint = Get-PortDebugHint -Port ([int]$env:WEB_PORT)
  $msg = ('docker compose failed. Likely a port conflict. Try setting WEB_PORT to another value, e.g. 8081.' + "`nCurrent WEB_PORT=" + $env:WEB_PORT)
  if ($hint) { $msg = $msg + "`n--- netstat ---`n" + $hint }
  throw $msg
}

Wait-ForComposeServicesRunning -ProjectName $localProjectName -ComposeFile 'docker-compose.local.yml' -Services @('api', 'web')
Wait-ForUrl -Url ('http://127.0.0.1:' + $env:API_PORT + '/api/health') -Name 'API'

Start-Process ('http://127.0.0.1:' + $env:WEB_PORT)

Write-Host ''
Write-Host 'Started.'
Write-Host 'Stop: double-click stop-wenxian.cmd (or run stop-wenxian.ps1)'
Write-Host ('Logs: cd "' + $scriptDir + '" ; docker compose -p "' + $localProjectName + '" -f docker-compose.local.yml logs -f')
