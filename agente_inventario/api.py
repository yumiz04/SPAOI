"""API HTTP del agente de inventario.

Envuelve el agente conversacional (``agente.responder``) en una API FastAPI para
poder conversar con él como usuario final sin usar la consola.

Endpoints:
    GET  /health            -> estado del servicio
    POST /chat              -> envía un mensaje y recibe la respuesta del agente
    POST /chat/reset        -> olvida el historial de una sesión
"""

from __future__ import annotations

import os
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agente import responder
from memoria import SimpleMemory

app = FastAPI(title="Agente de Inventario", version="1.0.0")

# Origenes permitidos para clientes web (el frontend de Vite corre en 5173).
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def _cors_origins() -> list[str]:
    raw = os.getenv("AGENT_CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

MAX_MESSAGES = 20
SESSIONS: dict[str, SimpleMemory] = {}
SESSIONS_LOCK = Lock()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensaje del usuario")
    session_id: str = Field(default="default", description="Identificador de la conversación")


class ChatResponse(BaseModel):
    session_id: str
    response: str


class ResetRequest(BaseModel):
    session_id: str = Field(default="default")


def _get_memory(session_id: str) -> SimpleMemory:
    """Devuelve (o crea) la memoria de una sesión, protegida por lock."""

    with SESSIONS_LOCK:
        memory = SESSIONS.get(session_id)
        if memory is None:
            memory = SimpleMemory(max_messages=MAX_MESSAGES)
            SESSIONS[session_id] = memory
        return memory


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    """Conversa con el agente manteniendo el historial por ``session_id``."""

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    memory = _get_memory(payload.session_id)
    answer = responder(memory, message)
    return ChatResponse(session_id=payload.session_id, response=answer or "")


@app.post("/chat/reset")
def reset(payload: ResetRequest) -> dict:
    """Borra el historial de la sesión indicada."""

    with SESSIONS_LOCK:
        SESSIONS.pop(payload.session_id, None)
    return {"session_id": payload.session_id, "status": "reset"}
