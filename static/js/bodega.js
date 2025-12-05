// SCRIPT PRINCIPAL DE BODEGA
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("scanInput");
    input.focus();

    let herramientaID = null;
    let mecanicoID = null;

    // Mantener foco constante
    setInterval(() => input.focus(), 500);

    input.addEventListener("input", async () => {
        const codigo = input.value.trim();
        if (!codigo) return;

        const res = await fetch("/bodega/scan", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({codigo})
        });

        const data = await res.json();

        if (data.error) {
            console.warn("SCAN ERROR:", data.error);
            input.value = "";
            return;
        }

        // Identificar tipo de código escaneado
        if (data.tipo === "herramienta") {
            herramientaID = data.id;
        } else if (data.tipo === "mecanico") {
            mecanicoID = data.id;
        }

        // Cuando ya tenemos ambos → procesar movimiento
        if (herramientaID && mecanicoID) {
            procesarMovimiento(herramientaID, mecanicoID);
            herramientaID = null;
            mecanicoID = null;
        }

        input.value = "";
    });
});


// PRESTAR / DEVOLVER AUTOMÁTICO
async function procesarMovimiento(herramientaID, mecanicoID) {

    // Consultar estado de bodega
    const estado = await fetch("/bodega/estado");
    const est = await estado.json();

    // Detectar si la herramienta está prestada (al menos 1 préstamo activo)
    const estaPrestada = est.prestadas.some(p => p.herramienta_id === herramientaID);

    const endpoint = estaPrestada ? "/bodega/devolver" : "/bodega/prestar";

    const res = await fetch(endpoint, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            herramienta_id: herramientaID,
            mecanico_id: mecanicoID
        })
    });

    const data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    alert(data.mensaje);

    actualizarTablas();
}


// REFRESCAR LISTAS AUTOMÁTICAMENTE
async function actualizarTablas() {
    const res = await fetch("/bodega/estado");
    const data = await res.json();

    const tablaDisp = document.getElementById("tablaDisponibles");
    const tablaPrest = document.getElementById("tablaPrestadas");

    // ============================
    // TABLA DE DISPONIBLES
    // ============================
    tablaDisp.innerHTML = "";
    data.disponibles.forEach(h => {
        tablaDisp.innerHTML += `
            <tr>
                <td>${h.nombre}</td>
                <td>${h.codigo}</td>
                <td>${h.cantidad_disponible} / ${h.cantidad_total}</td>
                <td><span class="badge badge-disponible">Disponible</span></td>
            </tr>`;
    });


    // ============================
    // TABLA DE PRESTADAS
    // (AQUÍ VA EL CAMBIO IMPORTANTE)
    // ============================
    tablaPrest.innerHTML = "";
    data.prestadas.forEach(p => {
        tablaPrest.innerHTML += `
            <tr data-herramienta="${p.id}" data-mecanico="${p.mecanico_id}">
                <td>${p.nombre}</td>
                <td>${p.codigo}</td>
                <td>${p.mecanico}</td>
                <td>${p.tiempo} min</td>
                <td><span class="badge badge-prestada">Prestada</span></td>
            </tr>`;
    });

}