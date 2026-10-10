/**
 * ========================================================================================
 * 💀 APEX BROWSER KEEP-ALIVE WATCHDOG FOR GOOGLE COLAB 💀
 * ========================================================================================
 * INSTRUCCIONES DE USO:
 * 1. Abre tu cuaderno de Google Colab en Chrome / Edge / Brave.
 * 2. Presiona F12 (Herramientas de Desarrollador) y ve a la pestaña "Console".
 * 3. Pega este código completo y presiona ENTER.
 * 
 * EFECTOS:
 * - Emite un oscilador de audio inaudible (0.00001 vol) que engaña al navegador para que NUNCA
 *   suspenda ni ponga en reposo la pestaña en segundo plano (Zero Tab Throttling).
 * - Simula clicks y actividad DOM en el botón de conexión de Colab cada 60 segundos.
 * - Monitorea y reconecta automáticamente si aparece el modal "Are you still there?".
 * ========================================================================================
 */

(function initApexColabKeepAlive() {
    console.clear();
    console.log("%c[APEX HACKER] INICIANDO PROTOCOLO DE VITALIDAD 24/7 EN COLAB...", "color: #00ff66; font-size: 16px; font-weight: bold;");

    // 1. INYECTOR DE AUDIO SILENCIOSO (PREVIENE SUSPENSIÓN DE HILO EN CHROME/EDGE)
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        gain.gain.setValueAtTime(0.00001, audioCtx.currentTime); // Inaudible
        osc.frequency.setValueAtTime(440, audioCtx.currentTime);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        console.log("%c[+] Web Audio Engine activo: Tab Throttling neutralizado.", "color: #00e5ff;");
    } catch (e) {
        console.warn("[-] AudioContext bloqueado hasta interacción de usuario:", e);
    }

    // 2. SIMULADOR DE ACTIVIDAD DOM & RECONEXIÓN AUTOMÁTICA
    let tickCount = 0;
    const intervalMs = 60000; // Cada 60 segundos

    setInterval(() => {
        tickCount++;
        const now = new Date().toLocaleTimeString();

        // Buscar botón de conectar
        const connectBtn = document.querySelector("colab-connect-button");
        if (connectBtn) {
            connectBtn.click();
        }

        // Buscar diálogo de reconexión si Colab pregunta si sigues ahí
        const okButtons = document.querySelectorAll("mwc-button, paper-button");
        okButtons.forEach(btn => {
            const txt = (btn.innerText || "").toLowerCase();
            if (txt.includes("ok") || txt.includes("reconectar") || txt.includes("reconnect") || txt.includes("yes")) {
                btn.click();
                console.log(`%c[!] Modal de inactividad detectado y neutralizado a las ${now}`, "color: #ff0055; font-weight: bold;");
            }
        });

        console.log(`%c[VITALIDAD COLAB] Pulso #${tickCount} ejecutado a las ${now} | Estado: VIVO`, "color: #00ff66;");
    }, intervalMs);

    console.log("%c[+] Sistema Keep-Alive Armada montado. La pestaña permanecerá despierta permanentemente.", "color: #00ff66;");
})();
