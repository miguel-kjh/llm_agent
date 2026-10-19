from mcp.server.fastmcp import FastMCP

mcp = FastMCP("articulos")

# Datos ficticios para el ejemplo.
ARTICULOS = {
    "1": {
        "titulo": "Modelos pequeños para resumen parlamentario",
        "contenido": (
            "Este trabajo estudia modelos pequeños adaptados "
            "para resumir debates parlamentarios."
        ),
    },
    "2": {
        "titulo": "Clasificación de imágenes con redes convolucionales",
        "contenido": (
            "Este trabajo compara arquitecturas convolucionales "
            "para clasificar imágenes."
        ),
    },
}


@mcp.tool()
def buscar_articulos(tema: str) -> list[dict]:
    """Busca artículos cuyo título contenga el tema indicado."""
    return [
        {"id": identificador, "titulo": articulo["titulo"]}
        for identificador, articulo in ARTICULOS.items()
        if tema.lower() in articulo["titulo"].lower()
    ]


@mcp.tool()
def leer_articulo(id: str) -> str:
    """Devuelve el contenido completo de un artículo dado su identificador."""
    articulo = ARTICULOS.get(id)

    if articulo is None:
        return "No existe un artículo con ese identificador."

    return articulo["contenido"]


if __name__ == "__main__":
    mcp.run(transport="stdio")