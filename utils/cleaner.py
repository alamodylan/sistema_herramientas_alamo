def limpiar_codigo(codigo: str) -> str:
    """
    Limpia códigos escaneados eliminando:
    - saltos de línea
    - espacios
    - caracteres especiales como * - /
    - tabulaciones
    - unicode raro invisible
    - y deja el código en mayúsculas

    Deja el código EXACTO tal como está en la base.
    """
    if not codigo:
        return ""

    # Quitar caracteres invisibles extremadamente comunes
    codigo = (
        codigo.strip()
              .replace("\r", "")
              .replace("\n", "")
              .replace("\t", "")
              .replace(" ", "")
              .replace("*", "")
              .replace("-", "")
              .replace("/", "")
    )

    # Quitar caracteres unicode invisibles
    codigo = "".join(c for c in codigo if c.isalnum())

    return codigo.upper()