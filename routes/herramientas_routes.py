from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from models.base import db
from models.herramienta import Herramienta
from models.prestamo import Prestamo
from utils.decorators import admin_required
from utils.security import update_last_activity
from utils.cleaner import limpiar_codigo

herramientas_bp = Blueprint("herramientas", __name__, url_prefix="/herramientas")


# ───────────────────────────────────────────────
#   LISTA DE HERRAMIENTAS
# ───────────────────────────────────────────────
@herramientas_bp.route("/")
@login_required
def lista_herramientas():
    update_last_activity()

    herramientas = Herramienta.query.order_by(Herramienta.nombre.asc()).all()

    return render_template("herramientas.html", herramientas=herramientas)


# ───────────────────────────────────────────────
#   CREAR HERRAMIENTA (ADMIN)
# ───────────────────────────────────────────────
@herramientas_bp.route("/crear", methods=["POST"])
@login_required
@admin_required
def crear_herramienta():
    update_last_activity()

    nombre = request.form.get("nombre")
    codigo = limpiar_codigo(request.form.get("codigo"))
    cantidad = request.form.get("cantidad", type=int)

    # ⚠️ Corrección única: evitar que "0" o "" rompan la validación
    if not nombre or not codigo or cantidad is None:
        flash("Nombre, código y cantidad son obligatorios.", "error")
        return redirect(url_for("herramientas.lista_herramientas"))

    if cantidad <= 0:
        flash("La cantidad debe ser mayor a 0.", "error")
        return redirect(url_for("herramientas.lista_herramientas"))

    # Código único
    if Herramienta.query.filter_by(codigo=codigo).first():
        flash("El código ya está registrado en otra herramienta.", "error")
        return redirect(url_for("herramientas.lista_herramientas"))

    nueva = Herramienta(
        nombre=nombre,
        codigo=codigo,
        cantidad_total=cantidad,
        cantidad_disponible=cantidad
    )

    db.session.add(nueva)
    db.session.commit()

    flash("Herramienta creada correctamente.", "success")
    return redirect(url_for("herramientas.lista_herramientas"))


# ───────────────────────────────────────────────
#   EDITAR HERRAMIENTA (ADMIN)
# ───────────────────────────────────────────────
@herramientas_bp.route("/editar/<int:id>", methods=["POST"])
@login_required
@admin_required
def editar_herramienta(id):
    update_last_activity()

    herramienta = Herramienta.query.get_or_404(id)

    nombre = request.form.get("nombre")
    codigo = request.form.get("codigo")
    cantidad_total = request.form.get("cantidad_total", type=int)

    # ⚠️ Corrección única
    if not nombre or not codigo or cantidad_total is None:
        flash("Nombre, código y cantidad total son obligatorios.", "error")
        return redirect(url_for("herramientas.lista_herramientas"))

    if cantidad_total <= 0:
        flash("La cantidad total debe ser mayor a 0.", "error")
        return redirect(url_for("herramientas.lista_herramientas"))

    # Validar código único en otro registro
    existe = Herramienta.query.filter(
        Herramienta.codigo == codigo,
        Herramienta.id != id
    ).first()

    if existe:
        flash("Este código ya está registrado por otra herramienta.", "error")
        return redirect(url_for("herramientas.lista_herramientas"))

    # Ajustar disponibilidad sin exceder
    diferencia = cantidad_total - herramienta.cantidad_total
    herramienta.cantidad_total = cantidad_total

    nueva_disponible = herramienta.cantidad_disponible + diferencia
    if nueva_disponible < 0:
        nueva_disponible = 0
    if nueva_disponible > cantidad_total:
        nueva_disponible = cantidad_total

    herramienta.cantidad_disponible = nueva_disponible

    herramienta.nombre = nombre
    herramienta.codigo = codigo

    db.session.commit()

    flash("Herramienta actualizada correctamente.", "success")
    return redirect(url_for("herramientas.lista_herramientas"))


# ───────────────────────────────────────────────
#   ELIMINAR HERRAMIENTA (ADMIN)
# ───────────────────────────────────────────────
@herramientas_bp.route("/eliminar/<int:id>", methods=["POST"])
@login_required
@admin_required
def eliminar_herramienta(id):
    update_last_activity()

    herramienta = Herramienta.query.get_or_404(id)

    # No eliminar si tiene historial
    if len(herramienta.prestamos) > 0:
        flash("Esta herramienta tiene historial de uso. No se puede eliminar.", "error")
        return redirect(url_for("herramientas.lista_herramientas"))

    db.session.delete(herramienta)
    db.session.commit()

    flash("Herramienta eliminada correctamente.", "success")
    return redirect(url_for("herramientas.lista_herramientas"))