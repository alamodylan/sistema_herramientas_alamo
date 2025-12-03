def limpiar_codigo(codigo: str) -> str:
    if not codigo:
        return ""

    return (
        codigo.strip()
              .replace("\r", "")
              .replace("\n", "")
              .replace("\t", "")
              .replace(" ", "")
              .replace("*", "")
              .replace("-", "")
              .replace("/", "")
              .upper()
    )