param(
    [string]$Branch = "codex/release-clean",
    [string]$OutputDir = "E:\",
    [switch]$Timestamped
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

Push-Location $repoRoot
try {
    $gitBranch = git branch --show-current
    if (-not $gitBranch) {
        throw "Not inside a git repository."
    }

    $baseName = "wenxian-release"
    if ($Timestamped) {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $baseName = "$baseName-$stamp"
    }

    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    }

    $outputPath = Join-Path $OutputDir "$baseName.tar.gz"
    git archive --format=tar.gz --output $outputPath $Branch
    Write-Output "Created package: $outputPath"
}
finally {
    Pop-Location
}
