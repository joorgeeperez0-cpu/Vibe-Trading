# Lanza un backtest usando un config concreto.
# Uso basico (signal engine por defecto = signal_engine_v1.py):
#   powershell -ExecutionPolicy Bypass -File mi_sistema\scripts\run_backtest.ps1 -ConfigName "in_sample_2018_2022"
# Uso con signal engine alternativo (test de sensibilidad):
#   powershell -ExecutionPolicy Bypass -File mi_sistema\scripts\run_backtest.ps1 -ConfigName "v15_cripto_top7_in_sample" -SignalEngine "signal_engine_v15_sma150"

param(
    [Parameter(Mandatory=$true)]
    [string]$ConfigName,
    [Parameter(Mandatory=$false)]
    [string]$SignalEngine = "signal_engine_v1"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$miSistemaDir = Split-Path -Parent $scriptDir
$repoRoot = Split-Path -Parent $miSistemaDir

$configFile = Join-Path $miSistemaDir "configs\$ConfigName.json"
$signalEngineFile = Join-Path $miSistemaDir "$SignalEngine.py"

# El nombre del run y carpeta de resultados incluye el signal engine si no es el default
$resultsSubdir = if ($SignalEngine -eq "signal_engine_v1") { $ConfigName } else { "$ConfigName" + "__" + $SignalEngine }
$resultsDir = Join-Path $miSistemaDir "results\$resultsSubdir"

if (-not (Test-Path $signalEngineFile)) {
    Write-Host "ERROR: no encuentro el signal engine $signalEngineFile" -ForegroundColor Red
    Write-Host "Signal engines disponibles en mi_sistema\:" -ForegroundColor Yellow
    Get-ChildItem $miSistemaDir -Filter "signal_engine*.py" | ForEach-Object { Write-Host "  $($_.BaseName)" }
    exit 1
}

if (-not (Test-Path $configFile)) {
    Write-Host "ERROR: no encuentro el config $configFile" -ForegroundColor Red
    Write-Host "Configs disponibles en mi_sistema\configs\:" -ForegroundColor Yellow
    Get-ChildItem (Join-Path $miSistemaDir "configs") -Filter "*.json" | ForEach-Object { Write-Host "  $($_.BaseName)" }
    exit 1
}

$runId = "manual_$resultsSubdir"
$runDirInContainer = "/app/agent/runs/$runId"

Set-Location $repoRoot

Write-Host ""
Write-Host "Config:        $ConfigName" -ForegroundColor Cyan
Write-Host "Signal engine: $SignalEngine" -ForegroundColor Cyan
Write-Host "Run ID:        $runId" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/7] Verificando contenedor..." -ForegroundColor Yellow
$containerId = docker compose ps -q vibe-trading
if (-not $containerId) {
    Write-Host "  ERROR: contenedor no esta corriendo. Lanza 'docker compose up -d' primero." -ForegroundColor Red
    exit 1
}
Write-Host "  Contenedor: $containerId" -ForegroundColor Green

Write-Host ""
Write-Host "[2/7] Creando run_dir en el contenedor..." -ForegroundColor Yellow
docker compose exec -T vibe-trading sh -c "rm -rf $runDirInContainer && mkdir -p $runDirInContainer/code"
Write-Host "  OK." -ForegroundColor Green

Write-Host ""
Write-Host "[3/7] Copiando config..." -ForegroundColor Yellow
docker cp $configFile "${containerId}:$runDirInContainer/config.json"
Write-Host "  OK." -ForegroundColor Green

Write-Host ""
Write-Host "[4/7] Copiando signal_engine_v1.py..." -ForegroundColor Yellow
docker cp $signalEngineFile "${containerId}:$runDirInContainer/code/signal_engine.py"
Write-Host "  OK." -ForegroundColor Green

Write-Host ""
Write-Host "[5/7] Verificando archivos..." -ForegroundColor Yellow
docker compose exec -T vibe-trading sh -c "ls $runDirInContainer && ls $runDirInContainer/code"

Write-Host ""
Write-Host "[6/7] Ejecutando backtest (1-3 minutos)..." -ForegroundColor Yellow
Write-Host ""
docker compose exec -T -w /app/agent vibe-trading python -m backtest.runner $runDirInContainer

Write-Host ""
Write-Host "[7/7] Trayendo artefactos..." -ForegroundColor Yellow
if (Test-Path $resultsDir) {
    Remove-Item -Recurse -Force $resultsDir
}
New-Item -ItemType Directory -Force -Path $resultsDir | Out-Null

$artifactsExists = docker compose exec -T vibe-trading sh -c "test -d $runDirInContainer/artifacts && echo SI || echo NO"
if ($artifactsExists.Trim() -eq "SI") {
    docker cp "${containerId}:$runDirInContainer/artifacts" "$resultsDir/"
    Write-Host "  Artefactos: $resultsDir\artifacts\" -ForegroundColor Green
} else {
    Write-Host "  ATENCION: no hay carpeta artifacts/." -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Comandos para validar:" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Metricas:" -ForegroundColor White
Write-Host "  Get-Content `"$resultsDir\artifacts\metrics.csv`"" -ForegroundColor Gray
Write-Host ""
Write-Host "Conteo de trades por ticker:" -ForegroundColor White
Write-Host "  Import-Csv `"$resultsDir\artifacts\trades.csv`" | Group-Object code | Select-Object Name, Count | Sort-Object Count -Descending" -ForegroundColor Gray
Write-Host ""
Write-Host "PnL cripto vs acciones:" -ForegroundColor White
Write-Host "  Import-Csv `"$resultsDir\artifacts\trades.csv`" | Where-Object { [decimal]`$_.pnl -ne 0 } | ForEach-Object { `$bloque = if (`$_.code -like '*USDT*') { 'cripto' } else { 'acciones' }; [PSCustomObject]@{ bloque = `$bloque; pnl = [decimal]`$_.pnl } } | Group-Object bloque | Select-Object Name, @{N='PnL';E={ (`$_.Group | Measure-Object -Property pnl -Sum).Sum }}, Count" -ForegroundColor Gray
Write-Host ""
Write-Host "PnL por ano:" -ForegroundColor White
Write-Host "  Import-Csv `"$resultsDir\artifacts\trades.csv`" | Where-Object { [decimal]`$_.pnl -ne 0 } | Group-Object { (`$_.timestamp -split '-')[0] } | Select-Object Name, @{N='PnL';E={ (`$_.Group | Measure-Object -Property pnl -Sum).Sum }}" -ForegroundColor Gray
