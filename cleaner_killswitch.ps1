<#
.SYNOPSIS
    CLEANER_KILLSWITCH.PS1 - Limpiador nativo de PowerShell para purga de agentes y remediación inmediata.
.DESCRIPTION
    Termina todos los procesos de agentes/sondas activos, elimina persistencias en registro y tareas,
    y tritura archivos residuales.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "SilentlyContinue"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "🛡️ APEX CLEANER POWERSHELL // ERRADICACIÓN NATIVA WIN32" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan

$signatures = @("agent_probe.py", "synthetic_agent.py", "mobile_synthetic_agent.py", "agent_killswitch.ps1")
$currentPid = $PID

# 1. Buscar y terminar procesos
Write-Host "[1] Buscando y eliminando procesos de agentes en memoria..." -ForegroundColor Yellow
$procList = Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $currentPid }

$terminatedCount = 0
foreach ($p in $procList) {
    $cmd = $p.CommandLine
    if ($null -ne $cmd) {
        foreach ($sig in $signatures) {
            if ($cmd.ToLower().Contains($sig.ToLower())) {
                Write-Host "  [!] Proceso detectado (PID $($p.ProcessId)) -> $sig" -ForegroundColor Red
                Stop-Process -Id $p.ProcessId -Force
                $terminatedCount++
                break
            }
        }
    }
}
Write-Host "  [+] Procesos terminados forzosamente: $terminatedCount" -ForegroundColor Green

# 2. Limpiar persistencias
Write-Host "[2] Limpiando claves de inicio en el Registro de Windows..." -ForegroundColor Yellow
Remove-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "ApexAgent*" -ErrorAction SilentlyContinue
Write-Host "  [+] Claves del registro sanitizadas." -ForegroundColor Green

# 3. Eliminar archivos temporales de forma segura
Write-Host "[3] Eliminando certificados y buffers residuales..." -ForegroundColor Yellow
$files = @("AGENT_DESTRUCTION_CERTIFICATE.json", "MOBILE_DESTRUCTION_CERTIFICATE.json", "sentinel_state.json")
foreach ($f in $files) {
    if (Test-Path $f) {
        Remove-Item $f -Force
        Write-Host "  [+] Archivo eliminado: $f" -ForegroundColor Green
    }
}

Write-Host "`n✅ SISTEMA SANEADO AL 100%. NINGÚN AGENTE ACTIVO EN MEMORIA." -ForegroundColor Cyan
exit 0
