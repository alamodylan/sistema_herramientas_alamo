from models.base import db


class Herramienta(db.Model):
    __tablename__ = "herramientas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(20), unique=True, nullable=False)

    # Cantidades
    cantidad_total = db.Column(db.Integer, nullable=False, default=1)
    cantidad_disponible = db.Column(db.Integer, nullable=False, default=1)

    # Estado para compatibilidad con el sistema original
    # Regla:
    #   - "Disponible" si cantidad_disponible > 0
    #   - "Prestada" si cantidad_disponible == 0
    estado = db.Column(db.String(20), nullable=False, default="Disponible")

    # ================================
    # Métodos de control de inventario
    # ================================

    def esta_disponible(self) -> bool:
        """True si hay unidades disponibles."""
        return self.cantidad_disponible > 0

    def prestar_unidad(self) -> bool:
        """
        Resta 1 a cantidad_disponible.
        Si llega a 0 → estado = 'Prestada'.
        Si sigue habiendo unidades → estado = 'Disponible'.
        """
        if self.cantidad_disponible > 0:
            self.cantidad_disponible -= 1

            if self.cantidad_disponible == 0:
                self.estado = "Prestada"
            else:
                self.estado = "Disponible"

            return True

        return False

    def devolver_unidad(self) -> bool:
        """
        Suma 1 a cantidad_disponible hasta el máximo (cantidad_total).
        Si vuelve al total → estado = 'Disponible'.
        """
        if self.cantidad_disponible < self.cantidad_total:
            self.cantidad_disponible += 1

            # Cuando vuelve a stock completo, la marcamos disponible.
            if self.cantidad_disponible == self.cantidad_total:
                self.estado = "Disponible"

            # Si queda en un punto intermedio (>0 y <total),
            # sigue siendo utilizable, por lo que mantenemos "Disponible".
            if self.cantidad_disponible > 0:
                self.estado = "Disponible"

            return True

        return False