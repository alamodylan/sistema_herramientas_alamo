def es_codigo_herramienta(codigo: str) -> bool:
    """
    Una herramienta SIEMPRE tiene código numérico.
    Ej: 10532, 44210, 90001
    """
    return codigo.isdigit()


def es_codigo_mecanico(codigo: str) -> bool:
    """
    Un mecánico SIEMPRE tiene código alfanumérico.
    Ej: M001, MECH-01, ALEX1
    """
    return any(c.isalpha() for c in codigo)