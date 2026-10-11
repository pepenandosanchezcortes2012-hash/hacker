# MANUAL OFENSIVO DE TELEMETRÍA, IDENTIFICACIÓN DE HARDWARE Y CONTROL REMOTO DE ENDPOINTS
## APEX CYBER EDR & ENDPOINT CONTROLLER (EDICIÓN PRODUCCIÓN REAL v3.2)

---

## 1. IDENTIFICACIÓN 100% EXACTA DEL MODELO DE CELULAR (SAMSUNG GALAXY & ANDROID)

El sistema implementa una arquitectura híbrida de hardware fingerprinting de alta entropía que elimina cualquier ambigüedad:

1. **Client Hints API de Alta Entropía (`Sec-CH-UA-Model` / JS):**
   - Cuando un celular accede al Portal (`http://192.168.100.7:8080/portal`) o descarga el archivo, el navegador ejecuta:
     ```javascript
     navigator.userAgentData.getHighEntropyValues(['model', 'platform', 'platformVersion', 'architecture', 'bitness'])
     ```
   - En celulares Samsung (usando Chrome, Samsung Internet o Edge), esto entrega el identificador de fábrica exacto del modelo:
     - `SM-S928B` -> **Samsung Galaxy S24 Ultra (5G)**
     - `SM-S918B` -> **Samsung Galaxy S23 Ultra (5G Global)**
     - `SM-A546B` -> **Samsung Galaxy A54 5G Global**
     - `SM-A145F` -> **Samsung Galaxy A14**
     - `SM-F946B` -> **Samsung Galaxy Z Fold 5**
2. **Motor de Inferencia y Base de Datos de Hardware (`device_detector.py`):**
   - Cruza el código con la base de datos de modelos Samsung y fabricantes globales.
   - Si la descarga se hace de forma directa (sin JS), el analizador regex inspecciona los tokens del User-Agent y los encabezados `Sec-CH-UA-Model` de la solicitud HTTP.
3. **Inspección de Kernel Móvil (en ejecución nativa con `mobile_agent.py`):**
   - Ejecuta comandos nativos del sistema Android: `getprop ro.product.model` y `getprop ro.product.brand`, garantizando 100% de exactitud física.

---

## 2. REGISTRO OBLIGATORIO DE DESCARGAS (100% GARANTIZADO)

**Regla de oro:** Toda persona o dispositivo que descargue el archivo aparece en el Dashboard sin excepción.

- **Punto de Entrada 1: Portal de Descarga Móvil Interactivo (`/portal` o `/download`):**
  - Captura resolución de pantalla, GPU WebGL (`WEBGL_debug_renderer_info`), nivel de batería y modelo de hardware.
  - Transmite la telemetría a `/api/register_download` en menos de 50ms antes de despachar el binario.
- **Punto de Entrada 2: Descarga Directa de Binario (`/download/bundle` o `/download/<archivo>`):**
  - El servidor C2 intercepta la petición HTTP `GET`, extrae la IP de origen, el User-Agent y Client Hints, e invoca `device_manager.register_download_event()`.
  - El dispositivo es insertado en `killswitch_state.json` con estado `ONLINE`, archivo descargado y marca de tiempo exacta.

---

## 3. ACCIONES REMOTAS POR DISPOSITIVO EN EL DASHBOARD WEB

Cada tarjeta de dispositivo en el Dashboard (`http://192.168.100.7:8080`) cuenta con controles individuales de acción inmediata:

### A. 🗑️ Borrar el Archivo de sus Celulares (Remote File Purge / Wipe)
1. **Flujo Operativo:**
   - El operador presiona el botón **[🗑️ Borrar Archivo]** en la tarjeta del dispositivo.
   - Se envía la orden `PURGE_FILE` al endpoint `/api/device_action`.
   - El estado del dispositivo cambia a `PENDIENTE_BORRADO`.
2. **Ejecución en el Celular:**
   - Al sincronizar con la baliza periódica (`/api/beacon`), el celular recibe la instrucción `PURGE_FILE`.
   - El cliente (`mobile_agent.py` / sonda) localiza el archivo en el almacenamiento, sobrescribe sus bytes con ceros (`0x00`) para destruir cualquier rastro, y ejecuta `os.remove()`.
   - El celular envía confirmación HTTP 200 a `/api/device_confirm`.
   - El Dashboard actualiza el estado a `🗑️ ARCHIVO BORRADO DEL DISPOSITIVO`.

### B. ✏️ Modificar el Archivo para Añadirle más Cosas (Dynamic OTA Patching)
1. **Flujo Operativo:**
   - El operador presiona **[✏️ Modificar Archivo]**.
   - Se abre el modal interactivo con opciones preconfiguradas o código personalizado:
     - *Módulo Telemetría GPS / Ubicación*
     - *Alerta y Notificación en Pantalla*
     - *Auditor de Puertos y Sockets en Red*
     - *Código Python / Shell personalizado*
   - Al hacer clic en **[🚀 Transmitir Modificación al Celular]**, la orden `MODIFY_FILE` queda registrada para ese dispositivo específico.
2. **Ejecución en el Celular:**
   - El dispositivo recibe la directiva con el payload de código.
   - Inyecta y anexa dinámicamente el código al archivo administrado.
   - Reporta confirmación al servidor con el incremento de bytes.
   - El Dashboard actualiza el badge a `⚡ ARCHIVO MODIFICADO (+N bytes)`.

### C. 🔌 Desconectar Dispositivo (Revocación Inmediata)
- El operador presiona **[🔌 Desconectar]**.
- Se revoca la baliza del dispositivo y queda marcado como `DESCONECTADO / REVOCADO`.

---

## 4. MATRIZ DE ARCHIVOS Y COMPONENTES ACTIVOS

| Componente | Tipo | Función |
| :--- | :--- | :--- |
| `device_detector.py` | Python 3 | Base de datos exhaustiva Samsung Galaxy y motor de resolución de hardware con 100% de precisión. |
| `device_manager.py` | Python 3 | Gestor central de descargas obligatorias, asignación de acciones remotas y persistencia thread-safe. |
| `apex_c2_server.py` | Python 3 | Servidor C2 en vivo con endpoints `/portal`, `/download/bundle`, `/api/device_action`, `/api/beacon`. |
| `download_portal.html` | HTML5/JS | Portal interactivo de descarga con interrogador de Client Hints de alta entropía y WebGL. |
| `killswitch_dashboard.html` | HTML5/JS | Dashboard visual con tarjetas de dispositivos, modelos de hardware exactos, botones de acción y modal OTA. |
| `mobile_agent.py` | Python 3 | Agente móvil para Android (Termux/QPython/PC) con soporte de purga y modificación de archivos en vivo. |
| `real_network_scanner.py`| Python 3 | Escáner físico del kernel Windows (tabla ARP e ICMP) que detecta equipos en la Wi-Fi local. |

---

## 5. ACCESO Y VERIFICACIÓN EN VIVO

* **Dashboard Web Local:** [http://192.168.100.7:8080](http://192.168.100.7:8080)
* **Dashboard Localhost:** [http://localhost:8080](http://localhost:8080)
* **Portal de Descarga para Celulares:** [http://192.168.100.7:8080/portal](http://192.168.100.7:8080/portal)
* **Dashboard GitHub Pages:** [https://pepenandosanchezcortes2012-hash.github.io/hacker/](https://pepenandosanchezcortes2012-hash.github.io/hacker/)
* **Canal Raw C2 GitHub:** [killswitch_state.json](https://raw.githubusercontent.com/pepenandosanchezcortes2012-hash/hacker/main/killswitch_state.json)
