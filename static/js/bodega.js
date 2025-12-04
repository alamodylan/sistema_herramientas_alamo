// SCRIPT PRINCIPAL DE BODEGA
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("scanInput");
    input.focus();

    let herramientaID = null;
    let mecanicoID = null;

    // Auto-focus permanente sin interferir
    setInterval(() => {
        if (document.activeElement !== input) input.focus();
    }, 300);

    input.addEventListener("input", async () => {
        const codigo = input.value.trim();
        if (!codigo) return;

        const res = await fetch("/bodega/scan", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({codigo})
        });

        const data = await res.json();

        // ❗ Si es lectura incompleta → ignorar sin romper nada
        if (data.partial) {
            return; // NO limpiar input todavía
        }

        // Limpiar input SOLO cuando la lectura es válida
        input.value = "";

        if (data.error) {
            // Puedes quitar este alert si quieres mensajes silenciosos
            alert(data.error);
            herramientaID = null;
            mecanicoID = null;
            return;
        }

        if (data.tipo === "herramienta") {
            herramientaID = data.id;
        } else if (data.tipo === "mecanico") {
            mecanicoID = data.id;
        }

        // Si ya tenemos los dos → prestar o devolver
        if (herramientaID && mecanicoID) {
            procesarMovimiento(herramientaID, mecanicoID);
            herramientaID = null;
            mecanicoID = null;
        }
    });
});

// PRESTAR / DEVOLVER AUTOMÁTICO
async function procesarMovimiento(herramientaID, mecanicoID) {

    // Obtener estado actual
    const estado = await fetch("/bodega/estado");
    const est = await estado.json();

    const estaPrestada = est.prestadas.some(p => p.id === herramientaID);

    const endpoint = estaPrestada ? "/bodega/devolver" : "/bodega/prestar";

    await fetch(endpoint, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            herramienta_id: herramientaID,
            mecanico_id: mecanicoID
        })
    });

    // Actualizar tablas siempre
    actualizarTablas();
}

// ACTUALIZAR TABLAS
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
                <td><span class="badge badge-disponible">Disponible</span></td>
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