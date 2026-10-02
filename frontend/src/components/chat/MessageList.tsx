import { useCallback, useEffect, useRef } from 'react';
import type { FC } from 'react';
import { MessageBubble } from './MessageBubble';
import { ThinkingIndicator } from './ThinkingIndicator';
import { UI_TEXT } from '../../data/mockData';
import type { ChatMessage } from '../../types/chat';

interface MessageListProps {
  readonly messages: readonly ChatMessage[];
  readonly isThinking: boolean;
}

/** Distancia al final (px) a partir de la cual seguimos al scroll automático. */
const PIN_THRESHOLD = 120;

/**
 * Lista desplazable de la conversación. El scroll automático solo se adhiere si el
 * usuario ya estaba cerca del final, para no interrumpir la lectura de respuestas largas.
 */
export const MessageList: FC<MessageListProps> = ({ messages, isThinking }) => {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const isPinnedRef = useRef(true);

  const handleScroll = useCallback(() => {
    const element = scrollRef.current;
    if (!element) {
      return;
    }
    const distance = element.scrollHeight - element.scrollTop - element.clientHeight;
    isPinnedRef.current = distance < PIN_THRESHOLD;
  }, []);

  useEffect(() => {
    const element = scrollRef.current;
    if (element && isPinnedRef.current) {
      element.scrollTop = element.scrollHeight;
    }
  }, [messages, isThinking]);

  return (
    <div
      aria-label={UI_TEXT.listRegion}
      className="min-h-0 flex-1 overflow-y-auto px-4 py-6 sm:px-6"
      onScroll={handleScroll}
      ref={scrollRef}
    >
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-5">
        {messages.map((message, index) => (
          <MessageBubble
            isLatest={index === messages.length - 1 && message.role === 'user'}
            key={message.id}
            message={message}
          />
        ))}
        <ThinkingIndicator isThinking={isThinking} />
      </div>
    </div>
  );
};

export default MessageList;