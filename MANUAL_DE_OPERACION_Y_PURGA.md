# MANUAL OFENSIVO DE TELEMETRÍA, CICLO DE VIDA DE IMPLANTES Y PURGA TOTAL
## APEX CYBER EDR & ENDPOINT CONTROLLER (EDICIÓN PRODUCCIÓN REAL)

---

## 1. ¿CÓMO FUNCIONA UN TROYANO / AGENTE DE ACCESO REMOTO (RAT) EN DISPOSITIVOS MÓVILES Y COMPUTADORAS?

### En Dispositivos Móviles (Android / Smartphones):
1. **Vector de Infiltración / Ingeniería Social:**
   - No ingresa por arte de magia: se camufla como un APK aparentemente legítimo (ej. actualizador de sistema, visor de archivos, parche de optimización o juego pirateado). Requiere que el usuario autorice "Orígenes desconocidos".
2. **Elevación de Privilegios Silenciosa:**
   - Una vez instalado, solicita permisos críticos:
     - **Servicio de Accesibilidad (`AccessibilityService`)**: Permite leer lo que aparece en pantalla, registrar pulsaciones de teclas (Keylogger) e interactuar automáticamente sin intervención del usuario.
     - **Exención de Optimización de Batería (`REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`)**: Evita que el sistema operativo mate el proceso cuando la pantalla se apague.
     - **Inicio Automático (`RECEIVE_BOOT_COMPLETED`)**: Se reactiva solo tras cada reinicio del teléfono.
3. **Canal de Comando y Control (Beaconing C2):**
   - El implante inicia conexiones salientes periódicas (HTTP/HTTPS o WebSockets) hacia el servidor maestro (`http://192.168.100.7:8080/api/beacon`). Dado que es tráfico saliente iniciado desde adentro de la red, los firewalls residenciales y el NAT lo permiten sin levantar alertas.
4. **Ejecución de Acciones:**
   - Reporta telemetría del teléfono (nivel de batería, dirección IP local, memoria, procesos) y queda a la espera de instrucciones.

### En Computadoras (Windows 11):
1. **Ejecución y Persistencia:**
   - Se inyecta en memoria o se registra en claves `Run` del Registro de Windows (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`) o en tareas programadas (`schtasks`).
2. **Evasión:**
   - Utiliza procesos legítimos del sistema o subprocesos desacoplados en segundo plano para evitar ser cerrado por el usuario común.

---

## 2. ¿CÓMO FUNCIONA EL ARCHIVO DE ELIMINACIÓN Y PURGA (KILL-SWITCH / CLEANER)?

El archivo `cleaner_killswitch.py` (y su contraparte nativa `cleaner_killswitch.ps1`):
1. **Inspección de Kernel y Memoria:**
   - Enumera la tabla de procesos activos (`Win32_Process`) buscando firmas de ejecución y puertos vinculados al C2.
2. **Interrupción Forzosa Atómica:**
   - Aplica terminación inmediata incondicional (`taskkill /F /PID` o `Stop-Process -Force`), cortando cualquier conexión de socket activa antes de que el agente pueda responder.
3. **Trituración Criptográfica de Archivos (Data Shredding):**
   - No se limita a borrar el archivo: sobrescribe los sectores del disco y archivos temporales con ceros binarios (`0x00`) para imposibilitar su recuperación forense.
4. **Sanitización del Registro y Autoarranque:**
   - Purga cualquier clave de persistencia en el registro o tarea programada.
5. **Certificado Forense de Limpieza:**
   - Emite confirmación formal con estado y código de salida 0.

---

## 3. MATRIZ DE ARCHIVOS DEL PAQUETE

| Archivo | Tipo | Propósito |
| :--- | :--- | :--- |
| `agent_probe.py` | Python 3 | Sonda multiplataforma de telemetría y balizas C2 (PC, Linux y Android Termux). |
| `agent_killswitch.ps1` | PowerShell | Sonda nativa para Windows 11 sin dependencias externas. |
| `cleaner_killswitch.py` | Python 3 | Herramienta de desinfección, matado forzoso en memoria y borrado seguro. |
| `cleaner_killswitch.ps1` | PowerShell | Limpiador y erradicador nativo para Windows 11. |
| `apex_c2_server.py` | Python 3 | Servidor HTTP C2 en vivo (`http://192.168.100.7:8080`). |
| `real_network_scanner.py`| Python 3 | Escáner real del kernel ARP de Windows para listar dispositivos de la red Wi-Fi. |

---

## 4. INSTRUCCIONES DE USO RÁPIDO

### Paso 1: Iniciar el Servidor de Control C2
```powershell
python apex_c2_server.py
```
Abre en tu navegador:
- Desde tu PC: `http://localhost:8080`
- Desde tu celular (conectado al mismo Wi-Fi): `http://192.168.100.7:8080`

### Paso 2: Ejecutar la Sonda de Prueba
```powershell
python agent_probe.py --server http://192.168.100.7:8080
```
Verás cómo tu dispositivo aparece en tiempo real en la página web con su batería, IP y telemetría.

### Paso 3: Erradicar Todo (Purga Inmediata)
- **Opción A (Desde la página web):** Pulsa el botón rojo **"DESCONEXIÓN TOTAL (KILL-SWITCH)"**. La sonda detectará la orden y se auto-destruirá al instante.
- **Opción B (Desde el script limpiador):** Ejecuta:
```powershell
python cleaner_killswitch.py
```
O en PowerShell:
```powershell
.\cleaner_killswitch.ps1
```
Todos los procesos se cerrarán forzosamente y el sistema quedará 100% limpio.
