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
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("scanInput");
    input.focus();

    let herramientaID = null;
    let mecanicoID = null;

    // Mantener foco en el input
    setInterval(() => input.focus(), 500);

    input.addEventListener("input", async () => {
        const codigo = input.value.trim();
        if (!codigo) return;

        const res = await fetch("/bodega/scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ codigo })
        });

        const data = await res.json();

        if (data.error) {
            showToast(data.error, "error");
            input.value = "";
            return;
        }

        if (data.tipo === "herramienta") {
            herramientaID = data.id;
        } else if (data.tipo === "mecanico") {
            mecanicoID = data.id;
        }

        // Cuando ya tenemos herramienta + mecánico, procesamos el movimiento
        if (herramientaID && mecanicoID) {
            await procesarMovimiento(herramientaID, mecanicoID);
            herramientaID = null;
            mecanicoID = null;
        }

        input.value = "";
    });
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