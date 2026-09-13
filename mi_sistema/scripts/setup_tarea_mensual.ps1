# Registra una tarea programada en Windows que lanza check_v2_etfs.py
# cada dia laborable a las 22:00 hora local, con el flag --only-if-last-business-day.
# El script Python solo actua realmente el ultimo dia habil de cada mes; el resto
# de dias sale silenciosamente. Asi se automatiza el rebalance mensual sin depender
# de que Windows Task Scheduler sepa cuando es "el ultimo dia habil del mes".
#
# Lanzar UNA SOLA VEZ con permisos elevados (clic derecho en PowerShell -> Ejecutar como administrador):
#   powershell -ExecutionPolicy Bypass -File mi_sistema\scripts\setup_tarea_mensual.ps1
#
# Para desinstalar la tarea:
#   Unregister-ScheduledTask -TaskName "Vibe v2 ETFs monthly check" -Confirm:$false

$ErrorActionPreference = "Stop"

$repoRoot = "C:\Users\user\Desktop\PROYECTOS\VIBE-TRADING\Vibe-Trading"
$scriptPath = Join-Path $repoRoot "mi_sistema\scripts\check_v2_etfs.py"
$logPath = Join-Path $repoRoot "mi_sistema\scripts\schedule_log_v2.txt"
$taskName = "Vibe v2 ETFs monthly check"

# Verificar Python
$pythonCmd = $null
foreach ($cmd in @("python", "py", "python3")) {
    try {
        & $cmd --version 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            break
        }
    } catch {}
}
if (-not $pythonCmd) {
    Write-Host "ERROR: no encuentro Python en el sistema." -ForegroundColor Red
    Write-Host "Instala Python primero: winget install Python.Python.3.12" -ForegroundColor Yellow
    exit 1
}
Write-Host "Python detectado: $pythonCmd" -ForegroundColor Green
Write-Host ""

if (-not (Test-Path $scriptPath)) {
    Write-Host "ERROR: no encuentro $scriptPath" -ForegroundColor Red
    exit 1
}

# Comando: cd al repo, python con flag, redirigir output a log
$argumentString = "-NoProfile -WindowStyle Hidden -Command `"cd '$repoRoot'; & $pythonCmd '$scriptPath' --only-if-last-business-day >> '$logPath' 2>&1`""

Write-Host "[1/3] Configurando triggers Lun-Vie a las 09:05..." -ForegroundColor Yellow
# Windows Task Scheduler no acepta "weekly Lun-Vie" en un solo trigger via cmdlet,
# construimos uno por dia y los pasamos como array
$triggers = @(
    New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday    -At "09:05"
    New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday   -At "09:05"
    New-ScheduledTaskTrigger -Weekly -DaysOfWeek Wednesday -At "09:05"
    New-ScheduledTaskTrigger -Weekly -DaysOfWeek Thursday  -At "09:05"
    New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday    -At "09:05"
)

Write-Host "[2/3] Configurando accion (PowerShell + Python con redireccion a log)..." -ForegroundColor Yellow
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argumentString

Write-Host "[3/3] Configurando settings (start when available, 5 min limit)..." -ForegroundColor Yellow
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopIfGoingOnBatteries `
    -AllowStartIfOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

# Eliminar tarea previa si existe
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "  Tarea previa encontrada, eliminando..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $triggers `
    -Settings $settings `
    -Description "Lanza check_v2_etfs.py --only-if-last-business-day cada dia laborable a las 09:05. El script Python solo escribe al log el ultimo dia habil del mes." `
    -Force | Out-Null

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Tarea registrada con exito" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Nombre:  $taskName"
Write-Host "  Trigger: Lun-Vie a las 09:05 (5 min despues de la tarea v1.5)"
Write-Host "  Flag:    --only-if-last-business-day (solo actua ultimo dia habil del mes)"
Write-Host "  Comando: $pythonCmd $scriptPath"
Write-Host "  Log:     $logPath"
Write-Host ""
Write-Host "Comprobar estado:"
Write-Host "  Get-ScheduledTask -TaskName '$taskName'"
Write-Host ""
Write-Host "Lanzar manualmente para probar (respetara el flag, o sea NO escribira salvo que hoy sea ultimo dia habil):"
Write-Host "  Start-ScheduledTask -TaskName '$taskName'"
Write-Host ""
Write-Host "Ver log de ejecuciones:"
Write-Host "  Get-Content '$logPath' -Tail 50"
Write-Host ""
Write-Host "Pausar sin borrar:"
Write-Host "  Disable-ScheduledTask -TaskName '$taskName'"
Write-Host ""
Write-Host "Eliminar:"
Write-Host "  Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
