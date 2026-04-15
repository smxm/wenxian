$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$localProjectName = 'literature-screening-local'

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
    throw 'docker not found.'
  }
}

function Stop-LegacyStacks {
  try { & docker compose -f docker-compose.local.yml down *> $null } catch {}
  try { & docker compose -f docker-compose.dev.yml down *> $null } catch {}
}

Ensure-DockerOnPath

$null = (& cmd /c "docker info >nul 2>&1")
if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop is not running.' }

Write-Host 'Stopping (local / stable mode)...'
Stop-LegacyStacks
& docker compose -p $localProjectName -f docker-compose.local.yml down
Write-Host 'Stopped.'
