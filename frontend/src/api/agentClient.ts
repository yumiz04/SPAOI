import { AGENT_FAILURE_PREFIXES } from '../data/mockData';
import type { AgentChatResponse } from '../types/chat';

/**
 * En desarrollo Vite hace de proxy hacia el agente, asi que usamos una ruta relativa
 * y evitamos CORS. Al servir el build desde otro dominio, define
 * VITE_AGENT_BASE_URL con la URL completa del agente (y habilita CORS en el agente).
 */
const BASE_PATH = import.meta.env.VITE_AGENT_BASE_URL ?? '/agent';

export class AgentApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'AgentApiError';
    this.status = status;
  }
}

function endpoint(path: string): string {
  return `${BASE_PATH}${path}`;
}

async function readError(response: Response): Promise<string> {
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return `El agente respondio HTTP ${response.status}.`;
  }

  if (typeof body === 'object' && body !== null) {
    const record = body as Record<string, unknown>;
    const detail = record.detail;

    if (typeof detail === 'string') {
      return detail;
    }

    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0];
      if (typeof first === 'object' && first !== null) {
        const message = (first as Record<string, unknown>).msg;
        if (typeof message === 'string') {
          return message;
        }
      }
    }

    if (typeof record.message === 'string') {
      return record.message;
    }
  }

  return `El agente respondio HTTP ${response.status}.`;
}

/** Envia un mensaje y devuelve la respuesta del agente. */
export async function sendMessage(
  sessionId: string,
  message: string,
  signal?: AbortSignal,
): Promise<AgentChatResponse> {
  const response = await fetch(endpoint('/chat'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
    signal,
  });

  if (!response.ok) {
    throw new AgentApiError(await readError(response), response.status);
  }

  return (await response.json()) as AgentChatResponse;
}

/** Le indica al agente que olvide el historial de la sesion. */
export async function resetSession(sessionId: string, signal?: AbortSignal): Promise<void> {
  const response = await fetch(endpoint('/chat/reset'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
    signal,
  });

  if (!response.ok) {
    throw new AgentApiError(await readError(response), response.status);
  }
}

/** Comprueba que el agente este vivo. */
export async function checkHealth(signal?: AbortSignal): Promise<boolean> {
  try {
    const response = await fetch(endpoint('/health'), { signal });
    return response.ok;
  } catch {
    return false;
  }
}

/** El agente devuelve HTTP 200 en fallos de modelo, asi que se detectan por el texto. */
export function isAgentFailure(text: string): boolean {
  const trimmed = text.trimStart();
  return AGENT_FAILURE_PREFIXES.some((prefix) => trimmed.startsWith(prefix));
}