// Mostrar notificación sin bloquear
function showToast(msg, tipo="ok") {
    const t = document.getElementById("toast");

    t.textContent = msg;
    t.className = "toast " + tipo;
    t.style.display = "block";

    setTimeout(() => {
        t.style.display = "none";
    }, 1600);
}

// SCRIPT PRINCIPAL DE BODEGA
input.addEventListener("input", async () => {
    const codigo = input.value.trim();
    if (!codigo) return;

    const res = await fetch("/bodega/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ codigo })
    });

    const data = await res.json();

    // ⚠️ Error REAL del backend: código no existe ni como herramienta ni como mecánico
    if (data.error) {
        showToast(data.error, "error");
        // Rompemos cualquier secuencia que estuviera empezada
        herramientaID = null;
        mecanicoID = null;
        input.value = "";
        return;
    }

    // ==========================================
    // 1) PRIMER ESCANEO (no hay nada guardado)
    // ==========================================
    if (!herramientaID && !mecanicoID) {

        // Si el primer código es de MECÁNICO → error
        if (data.tipo === "mecanico") {
            showToast("Primero debe escanear una herramienta.", "error");
            herramientaID = null;
            mecanicoID = null;
            input.value = "";
            return;
        }

        // Primer código correcto: herramienta
        if (data.tipo === "herramienta") {
            herramientaID = data.id;
            // No mostramos nada, solo esperamos al mecánico
            input.value = "";
            return;
        }
    }

    // ==========================================
    // 2) SEGUNDO ESCANEO (ya hay herramienta)
    // ==========================================
    if (herramientaID && !mecanicoID) {

        // Aquí ESPERAMOS un mecánico
        if (data.tipo !== "mecanico") {
            showToast("Luego debe escanear el código del mecánico.", "error");
            // Secuencia inválida, reseteamos todo
            herramientaID = null;
            mecanicoID = null;
            input.value = "";
            return;
        }

        // Correcto: segundo código es mecánico
        mecanicoID = data.id;
    }

    // ==========================================
    // 3) SI YA TENEMOS HERRAMIENTA + MECÁNICO
    // ==========================================
    if (herramientaID && mecanicoID) {
        await procesarMovimiento(herramientaID, mecanicoID);

        // Dejamos todo listo para la siguiente pareja de escaneos
        herramientaID = null;
        mecanicoID = null;
    }

    input.value = "";
});


// ============================
// PRESTAR / DEVOLVER AUTOMÁTICO
// ============================

async function procesarMovimiento(herramientaID, mecanicoID) {
    // Obtenemos el estado actual de bodega
    const estado = await fetch("/bodega/estado");
    const est = await estado.json();

    // Detectamos si ESTE mecánico ya tiene ESTA herramienta prestada
    const tienePrestamo = est.prestadas.some(
        p => p.herramienta_id === herramientaID && p.mecanico_id === mecanicoID
    );

    const endpoint = tienePrestamo ? "/bodega/devolver" : "/bodega/prestar";

    const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            herramienta_id: herramientaID,
            mecanico_id: mecanicoID
        })
    });

    const data = await res.json();

    if (data.error) {
        showToast(data.error, "error");
        return;
    }

    showToast(data.mensaje, "ok");
    actualizarTablas();
}


// ============================
// RECARGAR TABLAS
// ============================

async function actualizarTablas() {
    const res = await fetch("/bodega/estado");
    const data = await res.json();

    const tablaDisp = document.getElementById("tablaDisponibles");
    const tablaPrest = document.getElementById("tablaPrestadas");

    tablaDisp.innerHTML = "";
    data.disponibles.forEach(h => {
        tablaDisp.innerHTML += `
            <tr>
                <td>${h.nombre}</td>
                <td>${h.codigo}</td>
                <td>${h.cantidad_total}</td>
                <td>${h.cantidad_disponible}</td>
            </tr>`;
    });

    tablaPrest.innerHTML = "";
    data.prestadas.forEach(p => {
        tablaPrest.innerHTML += `
            <tr>
                <td>${p.nombre}</td>
                <td>${p.codigo}</td>
                <td>${p.mecanico}</td>
                <td>${p.tiempo} min</td>
                <td><span class="badge badge-prestada">Prestada</span></td>
            </tr>`;
    });
}