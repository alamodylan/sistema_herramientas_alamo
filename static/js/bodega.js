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

    // Si hay error real del backend (código no existe)
    if (data.error) {
        showToast(data.error, "error");
        input.value = "";
        return;
    }

    // 1) Asignar primero según el tipo
    if (data.tipo === "herramienta") {
        herramientaID = data.id;
    } 
    else if (data.tipo === "mecanico") {
        mecanicoID = data.id;
    }

    // 2) Validación del orden DESPUÉS de asignar

    // Si hay mecánico sin haber herramienta primero
    if (!herramientaID && mecanicoID) {
        showToast("El primer código debe ser una herramienta.", "error");
        mecanicoID = null;
        input.value = "";
        return;
    }

    // Si ya hay herramienta, el segundo escaneo debe ser mecánico
    if (herramientaID && !mecanicoID && data.tipo !== "mecanico") {
        showToast("El segundo código debe ser un mecánico.", "error");
        herramientaID = null;
        input.value = "";
        return;
    }

    // 3) Procesar préstamo/devolución solo si están ambos
    if (herramientaID && mecanicoID) {
        await procesarMovimiento(herramientaID, mecanicoID);
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