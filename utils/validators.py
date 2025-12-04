def es_codigo_herramienta(codigo: str) -> bool:
    """
    Una herramienta SIEMPRE tiene código numérico de 5 dígitos exactos.
    """
    return codigo.isdigit() and len(codigo) == 5


def es_codigo_mecanico(codigo: str) -> bool:
    """
    Un mecánico SIEMPRE tiene código con al menos una letra.
    """
    return any(c.isalpha() for c in codigo)