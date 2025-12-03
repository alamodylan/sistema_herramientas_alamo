import os
from datetime import timedelta

class Config:
    # ───────────────────────────────────────────────
    #   CONFIGURACIÓN GENERAL
    # ───────────────────────────────────────────────
    APP_NAME = "Sistema Herramientas Álamo"

    SECRET_KEY = os.getenv("SECRET_KEY", "clave-secreta-super-segura")

    # ───────────────────────────────────────────────
    #   BASE DE DATOS - POSTGRESQL (Render)
    # ───────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL").replace(
        "postgres://", "postgresql://"
    ) if os.getenv("DATABASE_URL") else "sqlite:///local.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ───────────────────────────────────────────────
    #   CONTROL DE SESIONES
    # ───────────────────────────────────────────────
    REMEMBER_COOKIE_DURATION = timedelta(days=7)

    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.getenv("INACTIVITY_MINUTES", 60))
    )

    SESSION_PERMANENT = True

    # ───────────────────────────────────────────────
    #   CONFIGURACIÓN VISUAL / GLOBAL
    # ───────────────────────────────────────────────
    ITEMS_PER_PAGE = 20   # paginación en historial, mecánicos, etc.