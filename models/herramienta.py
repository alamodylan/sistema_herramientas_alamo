from models.base import db

class Herramienta(db.Model):
    __tablename__ = "herramientas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(20), unique=True, nullable=False)

    # NUEVOS CAMPOS
    cantidad_total = db.Column(db.Integer, nullable=False, default=1)
    cantidad_disponible = db.Column(db.Integer, nullable=False, default=1)

    # Mantengo estado por compatibilidad,
    # pero ya NO se usará para controlar disponibilidad.
    estado = db.Column(db.String(20), nullable=False, default="Disponible")

    # ================================
    # Métodos para manejo de cantidades
    # ================================
    def esta_disponible(self):
        """Devuelve True si hay unidades disponibles."""
        return self.cantidad_disponible > 0

    def prestar_unidad(self):
        """Reduce la cantidad disponible en 1 si es posible."""
        if self.cantidad_disponible > 0:
            self.cantidad_disponible -= 1
            return True
        return False

    def devolver_unidad(self):
        """Incrementa la cantidad disponible en 1 sin superar el total."""
        if self.cantidad_disponible < self.cantidad_total:
            self.cantidad_disponible += 1
            return True
        return False