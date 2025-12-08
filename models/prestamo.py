from models.base import db
from datetime import datetime


class Prestamo(db.Model):
    __tablename__ = "prestamos"

    id = db.Column(db.Integer, primary_key=True)

    id_herramienta = db.Column(db.Integer, db.ForeignKey("herramientas.id"), nullable=False)
    id_mecanico = db.Column(db.Integer, db.ForeignKey("mecanicos.id"), nullable=False)

    fecha_prestamo = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    fecha_devolucion = db.Column(db.DateTime, nullable=True)

    # Tiempo total de uso en minutos
    tiempo_uso = db.Column(db.Integer, nullable=True)

    # Estados: Abierto / Cerrado
    estado = db.Column(db.String(20), nullable=False, default="Abierto")

    # Cantidad prestada (por ahora manejamos 1 por préstamo)
    cantidad = db.Column(db.Integer, nullable=False, default=1)

    # Relaciones
    herramienta = db.relationship("Herramienta", backref="prestamos", lazy=True)
    mecanico = db.relationship("Mecanico", backref="prestamos", lazy=True)

    def cerrar_prestamo(self):
        """Cierra el préstamo, calculando el tiempo de uso."""
        self.fecha_devolucion = datetime.utcnow()
        diff = self.fecha_devolucion - self.fecha_prestamo
        self.tiempo_uso = int(diff.total_seconds() // 60)
        self.estado = "Cerrado"