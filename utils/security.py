from flask import session
from flask_login import current_user
from datetime import datetime, timedelta
from config import Config

# ───────────────────────────────────────────────
#   CONTROL DE INACTIVIDAD
# ───────────────────────────────────────────────

def update_last_activity():
    """
    Actualiza la última actividad del usuario.
    Retorna False si la sesión debe ser cerrada.
    """
    if not current_user.is_authenticated:
        return True

    ahora = datetime.utcnow()
    ultimo = session.get("last_activity")

    if ultimo:
        ultimo_dt = datetime.fromisoformat(ultimo)
        diff = ahora - ultimo_dt

        if diff > timedelta(minutes=Config.INACTIVITY_MINUTES):
            return False  # Sesión expirada

    session["last_activity"] = ahora.isoformat()
    return True


def setup_inactivity_handler(app):
    """
    Registra una ruta /ping que mantiene viva la sesión.
    auth.js la usa cada vez que el usuario mueve el mouse.
    """
    @app.route("/ping")
    def ping():
        update_last_activity()
        return "ok", 200