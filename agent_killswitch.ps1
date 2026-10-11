<#
================================================================================
AGENT_KILLSWITCH.PS1 - AGENTE AUTÓNOMO WIN32 POWERSHELL CON WATCHDOG
================================================================================
Autor: APEX Autonomous Systems & Defensive Engineering
Objetivo: Windows 11 / Windows Server
Función:
    Agente de telemetría benigno en PowerShell nativo.
    Consulta el estado del interruptor en GitHub / local y ejecuta purga inmediata
    cuando detecta la señal de auto-destrucción (PURGE).
================================================================================
#>

[CmdletBinding()]
param(
    [string]$NodeId = "NODE_WIN11_HOST",
    [double]$IntervalSeconds = 3.0,
    [switch]$KillNow,
    [int]$MaxCycles = 0
)

$KillSwitchUrl = "https://raw.githubusercontent.com/pepenandosanchezcortes2012-hash/hacker/main/killswitch_state.json"
$LocalFallback = "killswitch_state.json"
$ScratchFile = ".temp_$($NodeId.ToLower())_buffer.dat"

# Inicializar buffer temporal inofensivo
$testData = [System.Text.Encoding]::UTF8.GetBytes("APEX_TELEMETRY_STREAM_$NodeId`n" * 32)
[System.IO.File]::WriteAllBytes($ScratchFile, $testData)

function Invoke-SelfDestruct {
    param([string]$Token = "APEX-ZERO-PURGE-9921")

    Write-Host "`n[🚨 ALERTA CRÍTICA: KILL-SWITCH DETECTADO]" -ForegroundColor Red
    Write-Host "[*] Token de Purga Recibido: $Token" -ForegroundColor Yellow
    Write-Host "[*] Iniciando protocolo atómico de autodestrucción en nodo: $NodeId..." -ForegroundColor Cyan

    # 1. Sobrescritura segura con ceros
    if (Test-Path $ScratchFile) {
        $len = (Get-Item $ScratchFile).Length
        $zeroBytes = New-Object byte[] $len
        [System.IO.File]::WriteAllBytes($ScratchFile, $zeroBytes)
        Remove-Item -Path $ScratchFile -Force
        Write-Host "  [+] Buffer temporal sobrescrito con ceros y eliminado." -ForegroundColor Green
    }

    # 2. Certificado Forense
    $cert = [PSCustomObject]@{
        node_id               = $NodeId
        destruction_timestamp = (Get-Date).ToUniversalTime().ToString("o")
        purge_token           = $Token
        system                = "Windows PowerShell $($PSVersionTable.PSVersion)"
        status                = "COMPLETELY_PURGED_AND_DISARMED"
    }
    $cert | ConvertTo-Json -Depth 4 | Out-File -FilePath "DESTRUCTION_CERTIFICATE_PS.json" -Encoding utf8
    Write-Host "  [+] Certificado forense de erradicación generado: DESTRUCTION_CERTIFICATE_PS.json" -ForegroundColor Green
    Write-Host "[🛡️ PROCESO TERMINADO] El agente se ha auto-eliminado exitosamente.`n" -ForegroundColor Green
}

if ($KillNow) {
    Invoke-SelfDestruct -Token "MANUAL-PS-PURGE-TOKEN"
    exit 0
}

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "🚀 INICIANDO AGENTE POWERSHELL WIN32: $NodeId" -ForegroundColor Green
Write-Host "🌐 Endpoint de Kill-Switch: $KillSwitchUrl" -ForegroundColor White
Write-Host "⏱️ Frecuencia de Sondeo: ${IntervalSeconds}s" -ForegroundColor White
Write-Host "================================================================`n" -ForegroundColor Cyan

$cycle = 0
while ($true) {
    $cycle++
    if ($MaxCycles -gt 0 -and $cycle -gt $MaxCycles) {
        Write-Host "[INFO] Límite de ciclos alcanzado." -ForegroundColor Yellow
        break
    }

    $state = $null
    try {
        $state = Invoke-RestMethod -Uri $KillSwitchUrl -TimeoutSec 3 -ErrorAction Stop
    } catch {
        if (Test-Path $LocalFallback) {
            try {
                $raw = Get-Content -Path $LocalFallback -Raw -Encoding utf8
                $state = $raw | ConvertFrom-Json
            } catch {}
        }
    }

    if (-not $state) {
        $state = [PSCustomObject]@{
            status = "ACTIVE"
            kill_switch_engaged = $false
            purge_token = "APEX-ZERO-PURGE-9921"
        }
    }

    $status = "$($state.status)".ToUpper()
    $killEngaged = [bool]$state.kill_switch_engaged
    $token = if ($state.purge_token) { $state.purge_token } else { "APEX-ZERO-PURGE-9921" }
    $timeStr = (Get-Date).ToString("HH:mm:ss")

    if ($killEngaged -or ($status -in @("PURGE", "DESTROY", "KILL"))) {
        Invoke-SelfDestruct -Token $token
        exit 0
    } elseif ($status -in @("PAUSED", "STANDBY")) {
        Write-Host "[$timeStr] [🟡 STANDBY] Nodo $NodeId en modo hibernación. Sin tareas activas." -ForegroundColor Yellow
    } else {
        Write-Host "[$timeStr] [🟢 BEACON] Nodo $NodeId transmitiendo baliza de telemetría normal." -ForegroundColor Green
    }

    Start-Sleep -Seconds $IntervalSeconds
}
