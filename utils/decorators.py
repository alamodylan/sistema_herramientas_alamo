from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def admin_required(f):
    """Permite acceso solo a administradores."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Debe iniciar sesión.", "error")
            return redirect(url_for("auth.login"))

        if not current_user.es_admin():
            flash("Acceso denegado. Solo administradores.", "error")
            return redirect(url_for("bodega.bodega"))

        return f(*args, **kwargs)
    return decorated_function


def role_required(role):
    """Permite acceso a un rol específico, útil por si se amplían roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Debe iniciar sesión.", "error")
                return redirect(url_for("auth.login"))

            if current_user.rol != role:
                flash("No tiene permisos para acceder a esta sección.", "error")
                return redirect(url_for("bodega.bodega"))

            return f(*args, **kwargs)
        return decorated_function
    return decorator