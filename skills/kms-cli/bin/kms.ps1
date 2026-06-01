$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExePath = Join-Path $ScriptDir "kms.exe"
$ConfigPath = Join-Path (Split-Path -Parent $ScriptDir) "config\config.toml"

if (-not (Test-Path $ExePath)) {
    Write-Error "未找到 kms.exe: $ExePath"
    exit 1
}

$hasConfigArg = $false
foreach ($arg in $args) {
    if ($arg -eq "--config" -or $arg.StartsWith("--config=")) {
        $hasConfigArg = $true
        break
    }
}

if ((-not $hasConfigArg) -and (Test-Path $ConfigPath)) {
    & $ExePath --config $ConfigPath @args
} else {
    & $ExePath @args
}

exit $LASTEXITCODE
