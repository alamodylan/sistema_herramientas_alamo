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
import pytz   # ← zona horaria CR
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

    # AHORA: disponibles por cantidad, no por estado
    herramientas_disponibles = Herramienta.query.filter(
        Herramienta.cantidad_disponible > 0
    ).all()

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
    codigo = limpiar_codigo(request.json.get("codigo", ""))

    print("DEBUG — RAW:", repr(request.json.get("codigo", "")))
    print("DEBUG — CLEAN:", repr(codigo))

    if not codigo:
        return jsonify({"error": "Código vacío"}), 400

    # Ignorar lecturas incompletas (lector mandando 1 → 18 → 182...)
    if codigo.isdigit() and len(codigo) < 5:
        return jsonify({"partial": True}), 200

    herramienta = Herramienta.query.filter_by(codigo=codigo).first()
    if herramienta:
        return jsonify({"tipo": "herramienta", "id": herramienta.id})

    mecanico = Mecanico.query.filter_by(codigo=codigo).first()
    if mecanico:
        return jsonify({"tipo": "mecanico", "id": mecanico.id})

    if es_codigo_herramienta(codigo):
        return jsonify({"error": "Herramienta no registrada."}), 404

    if es_codigo_mecanico(codigo):
        return jsonify({"error": "Mecánico no registrado."}), 404

    return jsonify({"error": "Código no reconocido."}), 400


# ───────────────────────────────────────────────
#   PRESTAR HERRAMIENTA (ENDPOINT CLÁSICO)
#   * Usa cantidades en lugar de estado *
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

    # AHORA: se valida por cantidad disponible
    if not herramienta.esta_disponible():
        return jsonify({"error": "No hay unidades disponibles de esta herramienta."}), 400

    # Crear préstamo (1 unidad)
    prestamo = Prestamo(
        id_herramienta=herramienta.id,
        id_mecanico=mecanico.id,
        fecha_prestamo=datetime.utcnow(),
        estado="Abierto"
    )

    # Descontar una unidad disponible
    herramienta.prestar_unidad()

    db.session.add(prestamo)
    db.session.commit()

    return jsonify({
        "ok": True,
        "mensaje": f"Herramienta {herramienta.nombre} prestada a {mecanico.nombre}"
    })


# ───────────────────────────────────────────────
#   DEVOLVER HERRAMIENTA (ENDPOINT CLÁSICO)
#   * Suma cantidad_disponible sin pasar de total *
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

    # Buscar préstamo activo de ESA herramienta con ESE mecánico
    prestamo = Prestamo.query.filter_by(
        id_herramienta=herramienta.id,
        id_mecanico=mecanico.id,
        estado="Abierto"
    ).first()

    if not prestamo:
        return jsonify({"error": "Esta herramienta no está registrada como prestada a este mecánico."}), 400

    # Cerrar préstamo y sumar unidad disponible
    prestamo.cerrar_prestamo()
    herramienta.devolver_unidad()

    db.session.commit()

    return jsonify({
        "ok": True,
        "mensaje": f"Herramienta {herramienta.nombre} devuelta por {mecanico.nombre}"
    })


# ───────────────────────────────────────────────
#   NUEVO ENDPOINT: MOVER AUTOMÁTICO
#   (decide prestar o devolver por pareja herramienta–mecánico)
# ───────────────────────────────────────────────
@bodega_bp.route("/movimiento", methods=["POST"])
@login_required
def movimiento_auto():
    """
    Si el mecánico YA tiene un préstamo abierto de esa herramienta → DEVOLVER UNA UNIDAD
    Si NO lo tiene → PRESTAR UNA UNIDAD (si hay stock disponible)
    """
    update_last_activity()

    id_herramienta = request.json.get("herramienta_id")
    id_mecanico = request.json.get("mecanico_id")

    herramienta = Herramienta.query.get(id_herramienta)
    mecanico = Mecanico.query.get(id_mecanico)

    if not herramienta or not mecanico:
        return jsonify({"error": "Datos inválidos"}), 400

    # ¿Ya hay un préstamo abierto para ESA pareja?
    prestamo_abierto = Prestamo.query.filter_by(
        id_herramienta=herramienta.id,
        id_mecanico=mecanico.id,
        estado="Abierto"
    ).first()

    # ── Caso 1: ya tenía → devolver UNA unidad
    if prestamo_abierto:
        prestamo_abierto.cerrar_prestamo()
        herramienta.devolver_unidad()
        db.session.commit()

        return jsonify({
            "ok": True,
            "accion": "devolucion",
            "mensaje": f"Herramienta {herramienta.nombre} devuelta por {mecanico.nombre}"
        })

    # ── Caso 2: NO tenía → prestar UNA unidad si hay stock
    if not herramienta.esta_disponible():
        return jsonify({"error": "No hay unidades disponibles de esta herramienta."}), 400

    nuevo = Prestamo(
        id_herramienta=herramienta.id,
        id_mecanico=mecanico.id,
        fecha_prestamo=datetime.utcnow(),
        estado="Abierto"
    )

    herramienta.prestar_unidad()
    db.session.add(nuevo)
    db.session.commit()

    return jsonify({
        "ok": True,
        "accion": "prestamo",
        "mensaje": f"Herramienta {herramienta.nombre} prestada a {mecanico.nombre}"
    })


# ───────────────────────────────────────────────
#   API - ESTADO DE BODEGA (HORA CR)
# ───────────────────────────────────────────────
@bodega_bp.route("/estado", methods=["GET"])
@login_required
def estado_bodega():
    update_last_activity()

    tz_cr = pytz.timezone("America/Costa_Rica")
    ahora_cr = datetime.now(tz_cr)

    # Disponibles = las que tienen unidades > 0
    disponibles = [{
        "id": h.id,
        "nombre": h.nombre,
        "codigo": h.codigo,
        "cantidad_total": h.cantidad_total,
        "cantidad_disponible": h.cantidad_disponible
    } for h in Herramienta.query.filter(Herramienta.cantidad_disponible > 0).all()]

    prestadas = []
    for p in Prestamo.query.filter_by(estado="Abierto").all():

        # Convertir fecha UTC de la base → hora Costa Rica
        fecha_prestamo_cr = p.fecha_prestamo.replace(tzinfo=pytz.utc).astimezone(tz_cr)

        minutos = int((ahora_cr - fecha_prestamo_cr).total_seconds() // 60)

        prestadas.append({
            "id": p.herramienta.id,
            "mecanico_id": p.mecanico.id,   # ← ★ CAMBIO AGREGADO ★
            "nombre": p.herramienta.nombre,
            "codigo": p.herramienta.codigo,
            "mecanico": p.mecanico.nombre,
            "tiempo": minutos
        })

    return jsonify({"disponibles": disponibles, "prestadas": prestadas})