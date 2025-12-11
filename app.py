from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from models.base import db
from models.usuario import Usuario
from routes.auth_routes import auth_bp
from routes.bodega_routes import bodega_bp
from routes.mecanicos_routes import mecanicos_bp
from routes.herramientas_routes import herramientas_bp
from routes.historial_routes import historial_bp
from utils.security import setup_inactivity_handler

# ───────────────────────────────────────────────
#   SISTEMA HERRAMIENTAS ÁLAMO - APP PRINCIPAL
# ───────────────────────────────────────────────

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar base de datos
    db.init_app(app)

    # Inicializar login
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Registrar Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(bodega_bp)
    app.register_blueprint(mecanicos_bp)
    app.register_blueprint(herramientas_bp)
    app.register_blueprint(historial_bp)

    # Cierre automático por inactividad
    setup_inactivity_handler(app)

     # Crear tablas si no existen (solo local)
    with app.app_context():
        db.create_all()

        # Crear usuario admin si no existe
        if not Usuario.query.filter_by(email="italamo@alamoterminales.com").first():
            admin = Usuario(
                nombre="Dylan Bustos",
                email="italamo@alamoterminales.com",
                rol="admin"
            )
            admin.set_password("atm4261*")
            db.session.add(admin)
            db.session.commit()
            print(">>> Usuario admin creado automáticamente")

        # 🔹 Crear usuario de BODEGA si no existe
        if not Usuario.query.filter_by(email="bodegasjo@alamoterminales.com").first():
            bodega_user = Usuario(
                nombre="Bodega SJO",
                email="bodegasjo@alamoterminales.com",
                rol="bodega"    # SOLO verá Bodega + Historial
            )
            bodega_user.set_password("atm8520")
            db.session.add(bodega_user)
            db.session.commit()
            print(">>> Usuario BODEGA creado automáticamente")

    return app


# Aplicación para Render / Gunicorn
app = create_app()

# ───────────────────────────────────────────────
#  REDIRECCIÓN DE HOME → /login
# ───────────────────────────────────────────────
@app.route("/")
def home_redirect():
    return redirect(url_for("auth.login"))

# ───────────────────────────────────────────────
#  MAIN LOCAL
# ───────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)