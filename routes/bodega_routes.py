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
import pytz   # ← ← ← AGREGADO PARA ZONA HORARIA CR
from pytz import timezone, utc

bodega_bp = Blueprint("bodega", __name__, url_prefix="/bodega")


# ───────────────────────────────────────────────
#  PANTALLA PRINCIPAL DE BODEGA
# ───────────────────────────────────────────────
@bodega_bp.route("/")
@login_required
def bodega():
    update_last_activity()

    cr = timezone("America/Costa_Rica")

    herramientas_disponibles = Herramienta.query.filter_by(estado="Disponible").all()
    prestamos_activos = Prestamo.query.filter_by(estado="Abierto").all()

    ahora_cr = datetime.utcnow().replace(tzinfo=utc).astimezone(cr)

    # Convertir fechas Y calcular minutos
    for p in prestamos_activos:
        if p.fecha_prestamo:
            hora_cr = p.fecha_prestamo.replace(tzinfo=utc).astimezone(cr)
            p.minutos = (ahora_cr - hora_cr).seconds // 60
        else:
            p.minutos = 0

    return render_template(
        "bodega.html",
        herramientas_disponibles=herramientas_disponibles,
        prestamos_activos=prestamos_activos,
    )

# ───────────────────────────────────────────────
#   API PARA ESCANEO
# ───────────────────────────────────────────────
@bodega_bp.route("/scan", methods=["POST"])
@login_required
def scan_code():
    update_last_activity()
    
    codigo_raw = request.json.get("codigo", "")
    codigo = limpiar_codigo(codigo_raw)

    print("DEBUG — RAW:", repr(codigo_raw))
    print("DEBUG — CLEAN:", repr(codigo))

    if not codigo:
        return jsonify({"error": "Código vacío"}), 400

    # ================================
    #   🔥 NUEVO: Filtrar rebotes
    # ================================
    # Filtrar SOLO números
    solo_digitos = "".join([c for c in codigo if c.isdigit()])

    # Ignorar lecturas incompletas del lector
    if len(solo_digitos) < 5:
        return jsonify({"partial": True}), 200

    # Si el lector manda más de 5 dígitos (doble lectura), cortar
    if len(solo_digitos) > 5:
        solo_digitos = solo_digitos[:5]

    # Sobrescribir código final
    codigo = solo_digitos

    print("DEBUG — FINAL:", repr(codigo))
    # ================================
    #   FIN DEL BLOQUE NUEVO
    # ================================

    # Buscar herramienta
    herramienta = Herramienta.query.filter_by(codigo=codigo).first()
    if herramienta:
        return jsonify({"tipo": "herramienta", "id": herramienta.id})

    # Buscar mecánico
    mecanico = Mecanico.query.filter_by(codigo=codigo).first()
    if mecanico:
        return jsonify({"tipo": "mecanico", "id": mecanico.id})

    # Validaciones según tipo
    if es_codigo_herramienta(codigo):
        return jsonify({"error": "Herramienta no registrada."}), 404

    if es_codigo_mecanico(codigo):
        return jsonify({"error": "Mecánico no registrado."}), 404

    return jsonify({"error": "Código no reconocido."}), 400


# ───────────────────────────────────────────────
#   PRESTAR HERRAMIENTA
# ───────────────────────────────────────────────
@bodega_bp.route("/prestar", methods=["POST"])
@login_required
def prestar_herramienta():
    update_last_activity()

    id_herramienta = request.json.get("herramienta_id")
    id_mecanico = request.json.get("mecanico_id")

    herramienta = Herramienta.query.get(id_herramienta)
    mecanico = Mecanico.query.get(id_mecanico)

    if not herramienta or not mecanico:
        return jsonify({"error": "Datos inválidos"}), 400

    if herramienta.estado == "Prestada":
        return jsonify({"error": "Esta herramienta ya está prestada."}), 400

    prestamo = Prestamo(
        id_herramienta=herramienta.id,
        id_mecanico=mecanico.id,
        fecha_prestamo=datetime.utcnow(),
        estado="Abierto"
    )
    herramienta.estado = "Prestada"

    db.session.add(prestamo)
    db.session.commit()

    return jsonify({
        "ok": True,
        "mensaje": f"Herramienta {herramienta.nombre} prestada a {mecanico.nombre}"
    })


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

    prestamo = Prestamo.query.filter_by(
        id_herramienta=herramienta.id,
        id_mecanico=mecanico.id,
        estado="Abierto"
    ).first()

    if not prestamo:
        return jsonify({"error": "Esta herramienta no está registrada como prestada a este mecánico."}), 400

    prestamo.cerrar_prestamo()
    herramienta.estado = "Disponible"

    db.session.commit()

    return jsonify({
        "ok": True,
        "mensaje": f"Herramienta {herramienta.nombre} devuelta por {mecanico.nombre}"
    })


# ───────────────────────────────────────────────
#   API - ESTADO DE BODEGA (CAMBIADO A HORA CR)
# ───────────────────────────────────────────────
@bodega_bp.route("/estado", methods=["GET"])
@login_required
def estado_bodega():
    update_last_activity()

    tz_cr = pytz.timezone("America/Costa_Rica")
    ahora_cr = datetime.now(tz_cr)

    disponibles = [{
        "id": h.id,
        "nombre": h.nombre,
        "codigo": h.codigo
    } for h in Herramienta.query.filter_by(estado="Disponible").all()]

    prestadas = []
    for p in Prestamo.query.filter_by(estado="Abierto").all():

        # Convertir fecha UTC de la base → hora Costa Rica
        fecha_prestamo_cr = p.fecha_prestamo.replace(tzinfo=pytz.utc).astimezone(tz_cr)

        minutos = int((ahora_cr - fecha_prestamo_cr).total_seconds() // 60)

        prestadas.append({
            "id": p.herramienta.id,
            "nombre": p.herramienta.nombre,
            "codigo": p.herramienta.codigo,
            "mecanico": p.mecanico.nombre,
            "tiempo": minutos
        })

    return jsonify({"disponibles": disponibles, "prestadas": prestadas})