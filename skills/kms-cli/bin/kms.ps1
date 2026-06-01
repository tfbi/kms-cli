$ErrorActionPreference = "Stop"

function Set-KmsUtf8Encoding {
    $utf8NoBom = New-Object System.Text.UTF8Encoding -ArgumentList $false
    $script:OutputEncoding = $utf8NoBom

    try {
        [Console]::OutputEncoding = $utf8NoBom
        [Console]::InputEncoding = $utf8NoBom
    } catch {
        # Some sandboxed hosts do not expose a normal console.
    }

    try {
        chcp.com 65001 > $null
    } catch {
        # chcp is only available in a normal Windows console.
    }
}

Set-KmsUtf8Encoding

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
