# Aplica el parche del loader cripto (OKX -> CCXT) dentro del contenedor Docker.
# Lanzar desde la raiz del repo:
#   powershell -ExecutionPolicy Bypass -File mi_sistema\scripts\parche_loader.ps1

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$miSistemaDir = Split-Path -Parent $scriptDir
$repoRoot = Split-Path -Parent $miSistemaDir
$patchScript = Join-Path $scriptDir "patch_loader.py"

Set-Location $repoRoot

Write-Host ""
Write-Host "[1/4] Verificando contenedor..." -ForegroundColor Yellow
$containerId = docker compose ps -q vibe-trading
if (-not $containerId) {
    Write-Host "  Contenedor no esta corriendo. Levantando..." -ForegroundColor Yellow
    docker compose --profile frontend up -d
    Start-Sleep -Seconds 8
    $containerId = docker compose ps -q vibe-trading
}
if (-not $containerId) {
    Write-Host "  ERROR: no se pudo levantar el contenedor." -ForegroundColor Red
    exit 1
}
Write-Host "  Contenedor: $containerId" -ForegroundColor Green

Write-Host ""
Write-Host "[2/4] Copiando patch_loader.py al contenedor..." -ForegroundColor Yellow
docker cp $patchScript "${containerId}:/tmp/patch_loader.py"
Write-Host "  OK." -ForegroundColor Green

Write-Host ""
Write-Host "[3/4] Aplicando parche..." -ForegroundColor Yellow
Write-Host ""
docker compose exec -T vibe-trading python /tmp/patch_loader.py

Write-Host ""
Write-Host "[4/4] Reiniciando contenedor..." -ForegroundColor Yellow
docker compose restart vibe-trading
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "Listo. El parche se mantiene mientras el contenedor exista." -ForegroundColor Green
Write-Host "Si haces 'docker compose down', se pierde y hay que volver a aplicarlo." -ForegroundColor Yellow
