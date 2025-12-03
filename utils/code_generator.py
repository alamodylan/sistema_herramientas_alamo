import random
import string

def generar_codigo_mecanico():
    # 6 dígitos aleatorios, como un código de barras sencillo
    return ''.join(random.choices(string.digits, k=6))