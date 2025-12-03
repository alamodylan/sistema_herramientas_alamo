from models.base import db

class Herramienta(db.Model):
    __tablename__ = "herramientas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(20), unique=True, nullable=False)  # Código de barras numérico
    estado = db.Column(db.String(20), nullable=False, default="Disponible")  
    # Estados: Disponible / Prestada

    def esta_disponible(self):
        return self.estado == "Disponible"