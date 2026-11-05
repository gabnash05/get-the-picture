$ErrorActionPreference = 'Stop'
$env:UV_CACHE_DIR = Join-Path $PSScriptRoot '.local/cache/uv'
$env:TEMP = Join-Path $PSScriptRoot '.local/tmp'
$env:TMP = $env:TEMP
$env:UV_PYTHON_DOWNLOADS = 'never'
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null

Push-Location $PSScriptRoot
try {
    uv run --frozen guesser-data @args
    $exitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $exitCode
