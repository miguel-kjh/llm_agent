import asyncio
import json
import sys
from pathlib import Path

from litellm import acompletion
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    # Indica cómo arrancar el servidor local.
    servidor = StdioServerParameters(
        command=sys.executable,
        args=["servidor.py"],
    )

    # El cliente arranca el servidor y se conecta a él.
    async with stdio_client(servidor) as (lectura, escritura):
        async with ClientSession(lectura, escritura) as session:
            await session.initialize()

            # 1. Descubrir las herramientas mediante MCP.
            catalogo = await session.list_tools()

            print(
                "Herramientas descubiertas:",
                [herramienta.name for herramienta in catalogo.tools],
            )

            # 2. Adaptar sus definiciones al formato de la API del LLM.
            herramientas = [
                {
                    "type": "function",
                    "function": {
                        "name": herramienta.name,
                        "description": herramienta.description or "",
                        "parameters": herramienta.inputSchema,
                    },
                }
                for herramienta in catalogo.tools
            ]

            mensajes = [
                {
                    "role": "system",
                    "content": (
                        "Eres un asistente de investigación. "
                        "Usa las herramientas para buscar artículos y leer "
                        "su contenido antes de resumirlos."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Busca artículos sobre modelos pequeños "
                        "y resume su contenido."
                    ),
                },
            ]

            # 3. Bucle del agente, limitado para evitar ciclos indefinidos.
            for _ in range(10):
                respuesta = await acompletion(
                    model="gpt-5-mini",
                    messages=mensajes,
                    tools=herramientas,
                )

                mensaje = respuesta.choices[0].message

                # Si no solicita herramientas, ya tenemos la respuesta.
                if not mensaje.tool_calls:
                    print("\nRespuesta final:")
                    print(mensaje.content)
                    return

                mensajes.append(
                    mensaje.model_dump(exclude_none=True)
                )

                # 4. Ejecutar las herramientas solicitadas por el LLM.
                for llamada in mensaje.tool_calls:
                    nombre = llamada.function.name
                    argumentos = json.loads(
                        llamada.function.arguments
                    )

                    print(f"\nEl LLM solicita: {nombre}({argumentos})")

                    resultado = await session.call_tool(
                        nombre,
                        arguments=argumentos,
                    )

                    # Serializamos el resultado MCP para dárselo al LLM.
                    contenido = resultado.model_dump_json()

                    # 5. Incorporar el resultado a la conversación.
                    mensajes.append({
                        "role": "tool",
                        "tool_call_id": llamada.id,
                        "content": contenido,
                    })

            print("Se alcanzó el límite de iteraciones.")


if __name__ == "__main__":
    asyncio.run(main())