from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models.base import db
from models.herramienta import Herramienta
from models.mecanico import Mecanico
from models.prestamo import Prestamo
from utils.cleaner import limpiar_codigo
from utils.decorators import admin_required
from utils.validators import (
    es_codigo_herramienta,
    es_codigo_mecanico,
)
from utils.security import update_last_activity
from datetime import datetime

bodega_bp = Blueprint("bodega", __name__, url_prefix="/bodega")


# ───────────────────────────────────────────────
#  PANTALLA PRINCIPAL DE BODEGA
# ───────────────────────────────────────────────
@bodega_bp.route("/")
@login_required
def bodega():
    update_last_activity()

    herramientas_disponibles = Herramienta.query.filter_by(estado="Disponible").all()
    prestamos_activos = Prestamo.query.filter_by(estado="Abierto").all()

    return render_template(
        "bodega.html",
        herramientas_disponibles=herramientas_disponibles,
        prestamos_activos=prestamos_activos,
    )


# ───────────────────────────────────────────────
#   API PARA ESCANEO (POST)
# ───────────────────────────────────────────────
@bodega_bp.route("/scan", methods=["POST"])
@login_required
def scan_code():
    update_last_activity()

    codigo_raw = request.json.get("codigo", "")
    codigo = limpiar_codigo(request.json.get("codigo", ""))

    if not codigo:
        return jsonify({"error": "Código vacío"}), 400

    # 1) ¿Es herramienta?
    if es_codigo_herramienta(codigo):
        herramienta = Herramienta.query.filter_by(codigo=codigo).first()
        if not herramienta:
            return jsonify({"error": "Herramienta no registrada."}), 404

        # Guardamos herramienta temporalmente en sesión
        # El front enviará luego el mecánico
        return jsonify({"tipo": "herramienta", "id": herramienta.id})

    # 2) ¿Es mecánico?
    if es_codigo_mecanico(codigo):
        mecanico = Mecanico.query.filter_by(codigo=codigo).first()
        if not mecanico:
            return jsonify({"error": "Mecánico no registrado."}), 404

        return jsonify({"tipo": "mecanico", "id": mecanico.id})

    return jsonify({"error": "Código no reconocido."}), 400


# ───────────────────────────────────────────────
#   PRESTAR HERRAMIENTA
# ───────────────────────────────────────────────
@bodega_bp.route("/scan", methods=["POST"])
@login_required
def scan_code():
    update_last_activity()

    codigo = limpiar_codigo(request.json.get("codigo", ""))

    if not codigo:
        return jsonify({"error": "Código vacío"}), 400

    # 🔹 1) PRIMERO buscar si existe como herramienta
    herramienta = Herramienta.query.filter_by(codigo=codigo).first()
    if herramienta:
        return jsonify({"tipo": "herramienta", "id": herramienta.id})

    # 🔹 2) Luego buscar si existe como mecánico
    mecanico = Mecanico.query.filter_by(codigo=codigo).first()
    if mecanico:
        return jsonify({"tipo": "mecanico", "id": mecanico.id})

    # 🔹 3) Si no existe en BD → recién ahí validamos qué tipo debió ser
    if es_codigo_herramienta(codigo):
        return jsonify({"error": "Herramienta no registrada."}), 404

    if es_codigo_mecanico(codigo):
        return jsonify({"error": "Mecánico no registrado."}), 404

    return jsonify({"error": "Código no reconocido."}), 400


# ───────────────────────────────────────────────
#   DEVOLVER HERRAMIENTA
# ───────────────────────────────────────────────
@bodega_bp.route("/devolver", methods=["POST"])
@login_required
def devolver_herramienta():
    update_last_activity()

    id_herramienta = request.json.get("herramienta_id")
    id_mecanico = request.json.get("mecanico_id")

    herramienta = Herramienta.query.get(id_herramienta)
    mecanico = Mecanico.query.get(id_mecanico)

    if not herramienta or not mecanico:
        return jsonify({"error": "Datos inválidos"}), 400

    # Buscar préstamo activo
    prestamo = Prestamo.query.filter_by(
        id_herramienta=herramienta.id,
        id_mecanico=mecanico.id,
        estado="Abierto"
    ).first()

    if not prestamo:
        return jsonify({"error": "Esta herramienta no está registrada como prestada a este mecánico."}), 400

    # Cerrar préstamo
    prestamo.cerrar_prestamo()
    herramienta.estado = "Disponible"

    db.session.commit()

    return jsonify({
        "ok": True,
        "mensaje": f"Herramienta {herramienta.nombre} devuelta por {mecanico.nombre}"
    })


# ───────────────────────────────────────────────
#   API - LISTA DINÁMICA DE BODEGA
#   (Actualización automática desde JS)
# ───────────────────────────────────────────────
@bodega_bp.route("/estado", methods=["GET"])
@login_required
def estado_bodega():
    update_last_activity()

    disponibles = [{
        "id": h.id,
        "nombre": h.nombre,
        "codigo": h.codigo
    } for h in Herramienta.query.filter_by(estado="Disponible").all()]

    prestadas = [{
        "id": p.herramienta.id,
        "nombre": p.herramienta.nombre,
        "codigo": p.herramienta.codigo,
        "mecanico": p.mecanico.nombre,
        "tiempo": (datetime.utcnow() - p.fecha_prestamo).seconds // 60
    } for p in Prestamo.query.filter_by(estado="Abierto").all()]

    return jsonify({"disponibles": disponibles, "prestadas": prestadas})