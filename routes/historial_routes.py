from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from models.base import db
from models.prestamo import Prestamo
from models.mecanico import Mecanico
from models.herramienta import Herramienta
from utils.security import update_last_activity
from datetime import datetime
from config import Config
from pytz import timezone   # ← IMPORTANTE

historial_bp = Blueprint("historial", __name__, url_prefix="/historial")

cr = timezone("America/Costa_Rica")   # ← ZONA HORARIA CR


@historial_bp.route("/")
@login_required
def historial():
    update_last_activity()

    mecanico_id = request.args.get("mecanico")
    herramienta_id = request.args.get("herramienta")
    fecha = request.args.get("fecha")

    page = request.args.get("page", 1, type=int)
    per_page = Config.ITEMS_PER_PAGE

    query = Prestamo.query.order_by(Prestamo.fecha_prestamo.desc())

    if mecanico_id and mecanico_id.isdigit():
        query = query.filter(Prestamo.id_mecanico == int(mecanico_id))

    if herramienta_id and herramienta_id.isdigit():
        query = query.filter(Prestamo.id_herramienta == int(herramienta_id))

    if fecha:
        try:
            fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
            query = query.filter(db.func.date(Prestamo.fecha_prestamo) == fecha_dt)
        except:
            pass

    prestamos = query.paginate(page=page, per_page=per_page, error_out=False)

    # -------------------------------------------------------
    #   🔥 CONVERTIR FECHAS A HORA DE COSTA RICA
    # -------------------------------------------------------
    for p in prestamos.items:
        if p.fecha_prestamo:
            p.fecha_prestamo = p.fecha_prestamo.astimezone(cr)

        if p.fecha_devolucion:
            p.fecha_devolucion = p.fecha_devolucion.astimezone(cr)

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