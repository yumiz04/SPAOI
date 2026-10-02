import { useCallback, useEffect, useRef, useState } from 'react';
import { isAgentFailure, resetSession, sendMessage } from '../api/agentClient';
import type { ChatMessage } from '../types/chat';

export interface UseChatResult {
  readonly messages: readonly ChatMessage[];
  readonly sessionId: string;
  readonly isThinking: boolean;
  readonly startNewConversation: () => void;
  readonly stop: () => void;
  readonly send: (text: string) => void;
}

function createMessageId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function createSessionId(): string {
  const suffix =
    typeof crypto !== 'undefined' && 'randomUUID' in crypto
      ? crypto.randomUUID()
      : Math.random().toString(36).slice(2);
  return `web-${suffix}`;
}

/**
 * Estado del chat: mensajes, sesion vigente y control de la peticion en vuelo.
 * Cada envio cancela el anterior para que nunca haya dos respuestas cruzadas.
 */
export function useChat(): UseChatResult {
  const [messages, setMessages] = useState<readonly ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string>(createSessionId);
  const [isThinking, setIsThinking] = useState(false);

  const controllerRef = useRef<AbortController | null>(null);
  const isThinkingRef = useRef(false);
  const sessionIdRef = useRef(sessionId);

  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  useEffect(() => () => controllerRef.current?.abort(), []);

  const stop = useCallback(() => {
    controllerRef.current?.abort();
  }, []);

  const startNewConversation = useCallback(() => {
    controllerRef.current?.abort();
    setMessages([]);
    setIsThinking(false);
    isThinkingRef.current = false;
    setSessionId(createSessionId());
    // El backend guarda el historial en memoria: se libera el contexto anterior.
    void resetSession(sessionIdRef.current).catch(() => undefined);
  }, []);

  const send = useCallback((raw: string) => {
    const text = raw.trim();
    if (!text || isThinkingRef.current) {
      return;
    }

    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    const replyId = createMessageId();
    const outgoing: ChatMessage = { id: createMessageId(), role: 'user', text, createdAt: Date.now(), status: 'sent' };
    const pending: ChatMessage = { id: replyId, role: 'agent', text: '', createdAt: Date.now(), status: 'pending' };

    setMessages((current) => [...current, outgoing, pending]);
    setIsThinking(true);
    isThinkingRef.current = true;

    void (async () => {
      try {
        const data = await sendMessage(sessionIdRef.current, text, controller.signal);
        const failed = isAgentFailure(data.response);

        setMessages((current) =>
          current.map((message) =>
            message.id === replyId
              ? { ...message, text: data.response, status: failed ? 'error' : 'sent' }
              : message,
          ),
        );
      } catch (error) {
        if (controller.signal.aborted) {
          setMessages((current) => current.filter((message) => message.id !== replyId));
        } else {
          const reason = error instanceof Error ? error.message : 'Error desconocido al contactar al agente.';
          setMessages((current) =>
            current.map((message) =>
              message.id === replyId ? { ...message, text: reason, status: 'error' } : message,
            ),
          );
        }
      } finally {
        setIsThinking(false);
        isThinkingRef.current = false;
      }
    })();
  }, []);

  return { messages, sessionId, isThinking, startNewConversation, stop, send };
}