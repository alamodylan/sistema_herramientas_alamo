from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models.usuario import Usuario
from models.base import db
from utils.security import update_last_activity

auth_bp = Blueprint("auth", __name__)


# ───────────────────────────────────────────────
#  LOGIN - MOSTRAR FORMULARIO
# ───────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("bodega.bodega"))
    return render_template("login.html")


# ───────────────────────────────────────────────
#  LOGIN - PROCESAR DATOS
# ───────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login_post():
    email = request.form.get("email").strip()
    password = request.form.get("password").strip()

    usuario = Usuario.query.filter_by(email=email).first()

    if not usuario or not usuario.check_password(password):
        flash("Credenciales incorrectas. Intente de nuevo.", "error")
        return redirect(url_for("auth.login"))

    login_user(usuario)
    update_last_activity()

    flash(f"Bienvenido {usuario.nombre}", "success")
    return redirect(url_for("bodega.bodega"))


# ───────────────────────────────────────────────
#  LOGOUT
# ───────────────────────────────────────────────
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()

    flash("Sesión finalizada correctamente.", "info")
    return redirect(url_for("auth.login"))


# ───────────────────────────────────────────────
#  VALIDADOR DE INACTIVIDAD
# ───────────────────────────────────────────────
@auth_bp.before_app_request
def validar_sesion():
    """
    Verifica inactividad REAL del usuario.
    Se ignoran rutas que no deben ejecutar este validador.
    """
    rutas_publicas = (
        "/login",
        "/logout",
        "/ping",
        "/static/",
    )

    # Evitar validación en rutas públicas
    if request.path.startswith(rutas_publicas):
        return

    # Si no está logueado → permitir que llegue al login
    if not current_user.is_authenticated:
        return

    # Validar inactividad
    if not update_last_activity():
        logout_user()
        session.clear()
        flash("Sesión cerrada por inactividad.", "warning")
        return redirect(url_for("auth.login"))


# ───────────────────────────────────────────────
#  RUTA RAÍZ "/" → REDIRIGE AUTOMÁTICAMENTE
# ───────────────────────────────────────────────
@auth_bp.route("/")
def home_redirect():
    """
    - Si NO está logueado → lo envía a /login
    - Si SÍ está logueado → lo envía a /bodega
    """
    if current_user.is_authenticated:
        return redirect(url_for("bodega.bodega"))
    return redirect(url_for("auth.login"))