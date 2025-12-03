from flask import session, request
from flask_login import current_user
from datetime import datetime, timedelta
from config import Config

# ───────────────────────────────────────────────
#   CONTROL DE INACTIVIDAD (OPTIMIZADO)
# ───────────────────────────────────────────────

def update_last_activity():
    """
    Actualiza la última actividad REAL del usuario.
    Evita que /ping y archivos estáticos saturen la sesión.
    Retorna False si la sesión debe cerrarse.
    """
    if not current_user.is_authenticated:
        return True

    # Ignorar rutas que NO son actividad real
    rutas_ignoradas = ("/ping", "/static/")
    if request.path.startswith(rutas_ignoradas):
        return True

    ahora = datetime.utcnow()
    ultimo = session.get("last_activity")

    if ultimo:
        ultimo_dt = datetime.fromisoformat(ultimo)
        diff = ahora - ultimo_dt

        # Si pasó el tiempo permitido → cerrar sesión
        if diff > timedelta(minutes=Config.INACTIVITY_MINUTES):
            return False

    # Registrar actividad real
    session["last_activity"] = ahora.isoformat()
    return True


def setup_inactivity_handler(app):
    """
    Ruta /ping que NO genera actividad,
    solo mantiene la página viva sin resetear sesión.
    """
    @app.route("/ping")
    def ping():
        return "ok", 200