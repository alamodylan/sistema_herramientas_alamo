from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models.base import db
from models.mecanico import Mecanico
from utils.decorators import admin_required
from utils.security import update_last_activity
from utils.code_generator import generar_codigo_mecanico

mecanicos_bp = Blueprint("mecanicos", __name__, url_prefix="/mecanicos")


# ───────────────────────────────────────────────
#   VISTA PRINCIPAL DE MECÁNICOS
# ───────────────────────────────────────────────
@mecanicos_bp.route("/")
@login_required
def lista_mecanicos():
    update_last_activity()

    mecanicos = Mecanico.query.order_by(Mecanico.nombre.asc()).all()

    return render_template("mecanicos.html", mecanicos=mecanicos)


# ───────────────────────────────────────────────
#   CREAR NUEVO MECÁNICO (ADMIN)
# ───────────────────────────────────────────────
@mecanicos_bp.route("/crear", methods=["POST"])
@login_required
@admin_required
def crear_mecanico():
    update_last_activity()

    nombre = request.form.get("nombre")
    codigo = request.form.get("codigo")  # puede venir vacío
    posicion = request.form.get("posicion")

    if not nombre:
        flash("El nombre es obligatorio.", "error")
        return redirect(url_for("mecanicos.lista_mecanicos"))

    # Si el admin NO escribe código, lo generamos automáticamente
    if not codigo or codigo.strip() == "":
        codigo = generar_codigo_mecanico()

    # Verificar código único
    if Mecanico.query.filter_by(codigo=codigo).first():
        flash("El código generado ya existe, intente nuevamente.", "error")
        return redirect(url_for("mecanicos.lista_mecanicos"))

    nuevo = Mecanico(nombre=nombre, codigo=codigo, posicion=posicion)

    db.session.add(nuevo)
    db.session.commit()

    flash(f"Mecánico agregado. Código asignado automáticamente: {codigo}", "success")
    return redirect(url_for("mecanicos.lista_mecanicos"))


# ───────────────────────────────────────────────
#   EDITAR MECÁNICO (ADMIN)
# ───────────────────────────────────────────────
@mecanicos_bp.route("/editar/<int:id>", methods=["POST"])
@login_required
@admin_required
def editar_mecanico(id):
    update_last_activity()

    mecanico = Mecanico.query.get_or_404(id)

    nombre = request.form.get("nombre")
    codigo = request.form.get("codigo")
    posicion = request.form.get("posicion")

    if not nombre or not codigo:
        flash("Nombre y código son obligatorios.", "error")
        return redirect(url_for("mecanicos.lista_mecanicos"))

    # Validar código único
    existe = Mecanico.query.filter(Mecanico.codigo == codigo, Mecanico.id != id).first()
    if existe:
        flash("El código ya existe en otro mecánico.", "error")
        return redirect(url_for("mecanicos.lista_mecanicos"))

    mecanico.nombre = nombre
    mecanico.codigo = codigo
    mecanico.posicion = posicion

    db.session.commit()

    flash("Mecánico actualizado correctamente.", "success")
    return redirect(url_for("mecanicos.lista_mecanicos"))


# ───────────────────────────────────────────────
#   ELIMINAR MECÁNICO (ADMIN)
# ───────────────────────────────────────────────
@mecanicos_bp.route("/eliminar/<int:id>", methods=["POST"])
@login_required
@admin_required
def eliminar_mecanico(id):
    update_last_activity()

    mecanico = Mecanico.query.get_or_404(id)

    # Seguridad: no eliminar si tiene herramientas prestadas
    if len(mecanico.prestamos) > 0:
        flash("Este mecánico tiene historial. No se puede eliminar.", "error")
        return redirect(url_for("mecanicos.lista_mecanicos"))

    db.session.delete(mecanico)
    db.session.commit()

    flash("Mecánico eliminado correctamente.", "success")
    return redirect(url_for("mecanicos.lista_mecanicos"))