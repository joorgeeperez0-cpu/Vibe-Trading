# Registra una tarea programada en Windows que lanza check_v15_cripto.py
# automaticamente todos los dias a las 09:00 hora local.
#
# Lanzar UNA SOLA VEZ con permisos elevados (clic derecho en PowerShell -> Ejecutar como administrador):
#   powershell -ExecutionPolicy Bypass -File mi_sistema\scripts\setup_tarea_diaria.ps1
#
# Para desinstalar la tarea mas adelante:
#   Unregister-ScheduledTask -TaskName "Vibe v1.5 daily check" -Confirm:$false

$ErrorActionPreference = "Stop"

$repoRoot = "C:\Users\user\Desktop\PROYECTOS\VIBE-TRADING\Vibe-Trading"
$scriptPath = Join-Path $repoRoot "mi_sistema\scripts\check_v15_cripto.py"
$logPath = Join-Path $repoRoot "mi_sistema\scripts\schedule_log.txt"
$taskName = "Vibe v1.5 daily check"

# Verificar que existe Python en el sistema
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

# Verificar que el script existe
if (-not (Test-Path $scriptPath)) {
    Write-Host "ERROR: no encuentro $scriptPath" -ForegroundColor Red
    exit 1
}

# Comando que ejecutara la tarea: cd al repo, luego python con redireccion de output a log
$argumentString = "-NoProfile -WindowStyle Hidden -Command `"cd '$repoRoot'; & $pythonCmd '$scriptPath' >> '$logPath' 2>&1`""

Write-Host "[1/3] Configurando trigger diario a las 09:00..." -ForegroundColor Yellow
$trigger = New-ScheduledTaskTrigger -Daily -At "09:00"

Write-Host "[2/3] Configurando accion (PowerShell que lanza Python con redireccion a log)..." -ForegroundColor Yellow
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argumentString

Write-Host "[3/3] Configurando settings (start when available para que se ejecute aunque el PC estuviera apagado a las 09:00)..." -ForegroundColor Yellow
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

# Registrar nueva tarea
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Lanza check_v15_cripto.py diariamente a las 09:00 hora local. Output en mi_sistema\scripts\schedule_log.txt" `
    -Force | Out-Null

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Tarea registrada con exito" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Nombre:  $taskName"
Write-Host "  Trigger: Diario a las 09:00"
Write-Host "  Comando: $pythonCmd $scriptPath"
Write-Host "  Log:     $logPath"
Write-Host ""
Write-Host "Comprobar estado de la tarea:"
Write-Host "  Get-ScheduledTask -TaskName '$taskName'"
Write-Host ""
Write-Host "Lanzarla manualmente para probar (sin esperar a las 09:00):"
Write-Host "  Start-ScheduledTask -TaskName '$taskName'"
Write-Host ""
Write-Host "Ver el log de las ejecuciones:"
Write-Host "  Get-Content '$logPath' -Tail 50"
Write-Host ""
Write-Host "Eliminar la tarea (si en algun momento quieres):"
Write-Host "  Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
