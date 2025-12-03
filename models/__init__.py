# Permite que Flask importe todos los modelos
from models.base import db
from models.usuario import Usuario
from models.herramienta import Herramienta
from models.mecanico import Mecanico
from models.prestamo import Prestamo