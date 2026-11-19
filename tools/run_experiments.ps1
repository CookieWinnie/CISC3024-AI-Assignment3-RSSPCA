$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:TEMP = Join-Path (Get-Location) 'tmp'
$env:TMP = $env:TEMP
$env:MPLCONFIGDIR = Join-Path $env:TEMP 'mpl'
$env:PIP_CACHE_DIR = Join-Path $env:TEMP 'cache'
& .\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider tests
if ($LASTEXITCODE -ne 0) { throw 'Numerical checks failed' }
& .\.venv\Scripts\python.exe -B -m experiments.run_all
if ($LASTEXITCODE -ne 0) { throw 'Experiments failed' }
& .\.venv\Scripts\python.exe -B -m src.visualization
if ($LASTEXITCODE -ne 0) { throw 'Figure generation failed' }
