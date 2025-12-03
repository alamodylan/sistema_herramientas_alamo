from models.base import db

class Mecanico(db.Model):
    __tablename__ = "mecanicos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(20), unique=True, nullable=False)  # Código alfanumérico
    posicion = db.Column(db.String(100), nullable=True)  # Ej: Soldador, Pintor, Mecánico General

    def __repr__(self):
        return f"<Mecanico {self.nombre}>"