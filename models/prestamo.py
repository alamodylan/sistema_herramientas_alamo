from models.base import db
from datetime import datetime

class Prestamo(db.Model):
    __tablename__ = "prestamos"

    id = db.Column(db.Integer, primary_key=True)

    id_herramienta = db.Column(db.Integer, db.ForeignKey("herramientas.id"), nullable=False)
    id_mecanico = db.Column(db.Integer, db.ForeignKey("mecanicos.id"), nullable=False)

    fecha_prestamo = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_devolucion = db.Column(db.DateTime, nullable=True)

    tiempo_uso = db.Column(db.Integer, nullable=True)  # tiempo total en minutos
    estado = db.Column(db.String(20), nullable=False, default="Abierto")  
    # Estados: Abierto / Cerrado

    # Relaciones
    herramienta = db.relationship("Herramienta", backref="prestamos", lazy=True)
    mecanico = db.relationship("Mecanico", backref="prestamos", lazy=True)

    def cerrar_prestamo(self):
        self.fecha_devolucion = datetime.utcnow()
        diff = self.fecha_devolucion - self.fecha_prestamo
        self.tiempo_uso = int(diff.total_seconds() // 60)  # minutos
        self.estado = "Cerrado"