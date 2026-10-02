export type MessageRole = 'user' | 'agent';

export type MessageStatus = 'sent' | 'pending' | 'error';

export interface ChatMessage {
  readonly id: string;
  readonly role: MessageRole;
  readonly text: string;
  readonly createdAt: number;
  readonly status: MessageStatus;
}

/** Respuesta de `POST /chat` del agente. */
export interface AgentChatResponse {
  readonly session_id: string;
  readonly response: string;
}

export type Theme = 'light' | 'dark';