from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from models.base import db
from models.prestamo import Prestamo
from models.mecanico import Mecanico
from models.herramienta import Herramienta
from utils.security import update_last_activity
from datetime import datetime
from config import Config

historial_bp = Blueprint("historial", __name__, url_prefix="/historial")


# ───────────────────────────────────────────────
#   VISTA PRINCIPAL DEL HISTORIAL
# ───────────────────────────────────────────────
@historial_bp.route("/")
@login_required
def historial():
    update_last_activity()

    # Filtros opcionales
    mecanico_id = request.args.get("mecanico")
    herramienta_id = request.args.get("herramienta")
    fecha = request.args.get("fecha")

    page = request.args.get("page", 1, type=int)
    per_page = Config.ITEMS_PER_PAGE

    # Query base
    query = Prestamo.query.order_by(Prestamo.fecha_prestamo.desc())

    # Filtro por mecánico
    if mecanico_id and mecanico_id.isdigit():
        query = query.filter(Prestamo.id_mecanico == int(mecanico_id))

    # Filtro por herramienta
    if herramienta_id and herramienta_id.isdigit():
        query = query.filter(Prestamo.id_herramienta == int(herramienta_id))

    # Filtro por fecha exacta
    if fecha:
        try:
            fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
            query = query.filter(
                db.func.date(Prestamo.fecha_prestamo) == fecha_dt
            )
        except:
            pass

    prestamos = query.paginate(page=page, per_page=per_page, error_out=False)

    mecanicos = Mecanico.query.order_by(Mecanico.nombre.asc()).all()
    herramientas = Herramienta.query.order_by(Herramienta.nombre.asc()).all()

    return render_template(
        "historial.html",
        prestamos=prestamos,
        mecanicos=mecanicos,
        herramientas=herramientas,
        filtros={
            "mecanico": mecanico_id,
            "herramienta": herramienta_id,
            "fecha": fecha
        }
    )


# ───────────────────────────────────────────────
#   API PARA OBTENER DETALLE DE UN PRÉSTAMO
# ───────────────────────────────────────────────
@historial_bp.route("/detalle/<int:id>", methods=["GET"])
@login_required
def detalle_prestamo(id):
    update_last_activity()

    prestamo = Prestamo.query.get_or_404(id)

    data = {
        "herramienta": prestamo.herramienta.nombre,
        "codigo_herramienta": prestamo.herramienta.codigo,
        "mecanico": prestamo.mecanico.nombre,
        "codigo_mecanico": prestamo.mecanico.codigo,
        "fecha_prestamo": prestamo.fecha_prestamo.strftime("%d/%m/%Y %H:%M"),
        "fecha_devolucion": (
            prestamo.fecha_devolucion.strftime("%d/%m/%Y %H:%M")
            if prestamo.fecha_devolucion else "Aún no devuelta"
        ),
        "tiempo_uso": f"{prestamo.tiempo_uso} minutos" if prestamo.tiempo_uso else "En uso",
        "estado": prestamo.estado
    }

    return jsonify(data)