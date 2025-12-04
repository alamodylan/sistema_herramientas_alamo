// SCRIPT PRINCIPAL DE BODEGA
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("scanInput");
    input.focus();

    let herramientaID = null;
    let mecanicoID = null;

    // Auto-focus estable
    setInterval(() => input.focus(), 400);

    input.addEventListener("input", async () => {
        const codigo = input.value.trim();
        if (!codigo) return;

        const res = await fetch("/bodega/scan", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({codigo})
        });

        const data = await res.json();

        // Si el scanner manda lecturas incompletas (1,18,182, etc)
        if (data.partial) {
            return; // No limpiar el input
        }

        // Limpiar input SOLO cuando el código está completo
        input.value = "";

        // Si hay error, lo mostramos y reiniciamos
        if (data.error) {
            // Puedes eliminar esta línea si no quieres alertas:
            // alert(data.error);
            herramientaID = null;
            mecanicoID = null;
            return;
        }

        // Clasificación correcta
        if (data.tipo === "herramienta") {
            herramientaID = data.id;
        }

        if (data.tipo === "mecanico") {
            mecanicoID = data.id;
        }

        // Si ya tenemos ambos → procesar
        if (herramientaID && mecanicoID) {
            await procesarMovimiento(herramientaID, mecanicoID);
            herramientaID = null;
            mecanicoID = null;
        }
    });
});

// PRESTAR / DEVOLVER AUTOMÁTICO
async function procesarMovimiento(herramientaID, mecanicoID) {

    const estado = await fetch("/bodega/estado");
    const est = await estado.json();

    const estaPrestada = est.prestadas.some(p => p.id === herramientaID);
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

    // Puedes eliminar esta línea para no mostrar alertas:
    // if (!data.error && data.mensaje) alert(data.mensaje);

    // Refrescar tablas SIEMPRE
    actualizarTablas();
}

// REFRESCAR TABLAS
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