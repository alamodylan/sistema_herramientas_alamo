import os
from datetime import timedelta

class Config:
    # ───────────────────────────────────────────────
    #   CONFIGURACIÓN GENERAL
    # ───────────────────────────────────────────────
    APP_NAME = "Sistema Herramientas Álamo"

    SECRET_KEY = os.getenv("SECRET_KEY", "clave-secreta-super-segura")

    # ───────────────────────────────────────────────
    #   BASE DE DATOS (Render/PostgreSQL o SQLite local)
    # ───────────────────────────────────────────────
    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL:
        # Render usa postgres:// pero SQLAlchemy requiere postgresql://
        SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace("postgres://", "postgresql://")
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///local.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ───────────────────────────────────────────────
    #   CONTROL DE SESIONES / INACTIVIDAD
    # ───────────────────────────────────────────────

    # Tiempo máximo de inactividad antes de cerrar sesión (por defecto 60 min)
    INACTIVITY_MINUTES = int(os.getenv("INACTIVITY_MINUTES", 60))

    # Flask requiere un lifetime general (esto NO controla la inactividad,
    # pero sirve para cookies y sesiones permanentes)
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=INACTIVITY_MINUTES)

    SESSION_PERMANENT = True

    # Mantiene la cookie "recordarme" por 7 días
    REMEMBER_COOKIE_DURATION = timedelta(days=7)

    # ───────────────────────────────────────────────
    #   CONFIGURACIÓN VISUAL / GLOBAL
    # ───────────────────────────────────────────────
    ITEMS_PER_PAGE = 20  # paginación en historial, mecánicos, bodega, etc.