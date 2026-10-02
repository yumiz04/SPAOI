from collections import deque
import datetime

class SimpleMemory:
    def __init__(self, max_messages=20):
        self.history = deque(maxlen=max_messages)

    def add_user(self, text):
        self.history.append({"role":"user", "content":text})

    def add_assistant(self, text, tool_calls=None):
        self.history.append({"role":"assistant", "content":text, "tool_calls":tool_calls})

    def add_tool(self, text, tool_call_id):
        self.history.append({"role":"tool", "content":text, "tool_call_id":tool_call_id})

    def add_log(self, role, text, tokens):
        self._log.append({"role":role, "content":text, "tokens":tokens})

    def pop_register(self):
         self.history.pop()

    def messages(self):
        return [self.build_system_prompt(), *list(self.history)]
    
    def log(self):
        return list(self._log)

    def build_system_prompt(self):
        ahora = datetime.datetime.now().astimezone()
        return {
            "role": "system",
            "content": f"""
                Agente de inventario. Usa solo las tools.
                Ahora: {datetime.datetime.now().astimezone()}
                No inventes datos. Pide solo argumentos obligatorios. Usa la tool adecuada. Reporta errores. Sé breve.
                Las fechas van en ISO (YYYY-MM-DD). Las propuestas de reposición o redistribución no ejecutan acciones.
            """
        }
        