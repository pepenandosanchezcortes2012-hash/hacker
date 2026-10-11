# APEX KILL-SWITCH C2 CONTROLLER // PLATAFORMA DE EMULACIÓN ADVERSARIA

## 1. Descripción de la Arquitectura
Este sistema implementa un **Interruptor Maestro (Kill-Switch)** y un entorno de emulación y validación de agentes con capacidad de desarmado y auto-destrucción atómica instantánea.

La plataforma consta de:
1. **Interruptor Web C2 (`index.html`)**: Dashboard interactivo alojado en GitHub Pages con switches de tres estados:
   - 🟢 `ACTIVE` (Monitoreo y balizas en tiempo real).
   - 🟡 `PAUSED` (Standby / Hibernación sin destrucción).
   - 🔴 `PURGE` (Auto-destrucción total e instantánea de todos los agentes).
2. **Canal de Señalización JSON (`killswitch_state.json`)**: Endpoint REST/JSON accesible en GitHub Raw.
3. **Agentes Autónomos Resilientes**:
   - [`synthetic_agent.py`](synthetic_agent.py) (Python multiplataforma).
   - [`agent_killswitch.ps1`](agent_killswitch.ps1) (PowerShell Win32 nativo para Windows 11).
   - [`mobile_synthetic_agent.py`](mobile_synthetic_agent.py) (Simulador Android / ADB).

---

## 2. Instrucciones de Ejecución

### Modo A: Ejecutar Agente en Windows 11 (Python)
```powershell
python synthetic_agent.py --node-id NODE_WIN11_HOST --interval 2.5
```

### Modo B: Ejecutar Agente en Windows 11 (PowerShell Nativo)
```powershell
.\agent_killswitch.ps1 -NodeId NODE_WIN11_HOST -IntervalSeconds 3
```

### Modo C: Simular Disparo Inmediato de Auto-Destrucción (Kill-Switch)
```powershell
python synthetic_agent.py --kill-now
```

---

## 3. Protocolo de Auto-Destrucción (Purga)
Cuando el interruptor cambia a `PURGE`:
1. El agente detecta el flag `kill_switch_engaged: true` y el token `APEX-ZERO-PURGE-9921`.
2. Sobrescribe inmediatamente todos sus buffers y archivos temporales con ceros binarios (`0x00`).
3. Genera un certificado forense inmutable (`DESTRUCTION_CERTIFICATE.json`) con firma criptográfica SHA-256.
4. Termina de forma limpia con código de salida `0`.
