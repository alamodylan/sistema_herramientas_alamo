from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models.base import db
from models.mecanico import Mecanico
from utils.decorators import admin_required
from utils.cleaner import limpiar_codigo
from utils.security import update_last_activity
from utils.code_generator import generar_codigo_mecanico
from flask import send_file
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io

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
    posicion = request.form.get("posicion")
    codigo = limpiar_codigo(request.form.get("codigo"))

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

# ───────────────────────────────────────────────
#   DESCARGAR CÓDIGO DE BARRAS DEL MECÁNICO
# ───────────────────────────────────────────────
@mecanicos_bp.route("/barcode/<int:id>", methods=["GET"])
@login_required
def descargar_barcode_mecanico(id):
    update_last_activity()

    mecanico = Mecanico.query.get_or_404(id)

    codigo = mecanico.codigo        # Ej: M001
    nombre = mecanico.nombre        # Ej: Juan Pérez

    # Crear código de barras en memoria
    Code128 = barcode.get_barcode_class('code128')

    buffer = io.BytesIO()
    code = Code128(codigo, writer=ImageWriter())

    # Guardar código de barras simple
    code.write(buffer)
    buffer.seek(0)

    barcode_img = Image.open(buffer)

    # Crear espacio adicional para el nombre
    width, height = barcode_img.size
    final_img = Image.new("RGB", (width, height + 40), "white")
    final_img.paste(barcode_img, (0, 0))

    draw = ImageDraw.Draw(final_img)

    try:
        font = ImageFont.truetype("arial.ttf", 22)
    except:
        font = ImageFont.load_default()

    # Centrar nombre
    text_w = draw.textlength(nombre, font=font)
    draw.text(((width - text_w) / 2, height + 5), nombre, fill="black", font=font)

    # Guardar imagen final
    output = io.BytesIO()
    final_img.save(output, format="PNG")
    output.seek(0)

    return send_file(
        output,
        mimetype="image/png",
        as_attachment=True,
        download_name=f"{codigo}_{nombre}.png"
    )