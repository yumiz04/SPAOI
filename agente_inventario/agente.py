from dotenv import load_dotenv
from memoria import SimpleMemory
from tools_inventory import INVENTORY_TOOLS, InventoryTools
import os
import json
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("API_OPENCODE_KEY"), base_url=os.getenv("API_OPENCODE_URL"))
MODEL = os.getenv("API_OPENCODE_MODEL")
MAX_TOKENS = int(os.getenv("API_OPENCODE_MAX_TOKENS", "4000"))

inventario = InventoryTools()

ALL_TOOLS = INVENTORY_TOOLS

_OP = {
    # Herramientas de inventario (SRS RF-25)
    "buscar_productos": inventario.buscar_productos,
    "obtener_existencias": inventario.obtener_existencias,
    "obtener_lotes": inventario.obtener_lotes,
    "obtener_movimientos": inventario.obtener_movimientos,
    "obtener_ventas": inventario.obtener_ventas,
    "obtener_compras": inventario.obtener_compras,
    "obtener_proveedores": inventario.obtener_proveedores,
    "analizar_inventario": inventario.analizar_inventario,
    "analizar_desabasto": inventario.analizar_desabasto,
    "analizar_caducidades": inventario.analizar_caducidades,
    "analizar_sobreinventario": inventario.analizar_sobreinventario,
    "analizar_rotacion": inventario.analizar_rotacion,
    "pronosticar_demanda": inventario.pronosticar_demanda,
    "estimar_fecha_agotamiento": inventario.estimar_fecha_agotamiento,
    "proponer_reposicion": inventario.proponer_reposicion,
    "proponer_redistribucion": inventario.proponer_redistribucion,
    "obtener_alertas": inventario.obtener_alertas,
    "crear_alerta": inventario.crear_alerta,
    "atender_alerta": inventario.atender_alerta,
}

memory = SimpleMemory(max_messages=20)

def responder(memory, text_user, MAX_TOOL_ROUNDS = 8):
    for ronda in range(MAX_TOOL_ROUNDS):
        memory.add_user(text=text_user)
        try:
            r = client.chat.completions.create(model=MODEL, messages=[*memory.messages()], tools=ALL_TOOLS, max_tokens=MAX_TOKENS)
        except Exception as exc:
            memory.pop_register()
            return f"No se puede comunicar con el agente ({type(exc).__name__}). Intentalo denuevo"
        
        msg = r.choices[0].message
        if msg.content:
            memory.add_assistant(text=msg.content)

        if not msg.tool_calls:
            return msg.content or ""
        
        memory.add_assistant(text=msg.content, tool_calls=[{"id": tc.id, "type": "function",
                            "function": {"name": tc.function.name,
                                        "arguments": tc.function.arguments}}
                        for tc in msg.tool_calls])

        for tc in msg.tool_calls:
            print(f"  [ronda {ronda+1}] {tc.function.name}({tc.function.arguments})")
            if tc.function.name in _OP:
                args = json.loads(tc.function.arguments)
                res = _OP[tc.function.name](**args)
                memory.add_tool(text=json.dumps(res, ensure_ascii=False), tool_call_id=tc.id)                   
            else:
                memory.add_tool(text={"success":False, "error":"No se encontro una herramienta adecuada"}, tool_call_id=-1)

    return "La operacion necesito demasiadas rondas..."
    

def main():
    memory = SimpleMemory()
    while True:
        text = input("Tu: ").strip()
        if text.lower() in ("salir", "exit", "quit"):
            break
        if text:
            print("Assistant: ", responder(memory, text))

if __name__ == "__main__":
    main()