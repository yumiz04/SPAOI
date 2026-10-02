import { Suspense, lazy } from 'react';
import type { FC } from 'react';
import { AlertIcon } from '../icons';
import { CopyButton } from './CopyButton';
import { UI_TEXT } from '../../data/mockData';
import type { ChatMessage } from '../../types/chat';

// react-markdown pesa lo suficiente como para sacarlo del bundle inicial.
const MarkdownRenderer = lazy(() => import('../markdown/MarkdownRenderer'));

interface MessageBubbleProps {
  readonly message: ChatMessage;
  readonly isLatest: boolean;
}

/** Burbuja de un turno de la conversacion: usuario a la derecha, agente a la izquierda. */
export const MessageBubble: FC<MessageBubbleProps> = ({ message, isLatest }) => {
  const isUser = message.role === 'user';
  const isError = message.status === 'error';

  const time = new Date(message.createdAt).toLocaleTimeString('es-MX', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <article
      className={`msg-auto flex w-full gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {!isUser ? (
        <div className="mt-1 flex size-8 flex-none items-center justify-center rounded-full bg-brand-soft text-xs font-semibold text-brand">
          AI
        </div>
      ) : null}

      <div className={`flex min-w-0 max-w-[min(46rem,88%)] flex-col gap-1.5 ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`w-full rounded-card px-4 py-3 shadow-soft ${
            isUser
              ? 'bg-brand text-brand-ink'
              : isError
                ? 'border border-danger/40 bg-danger-soft text-danger'
                : 'border border-line bg-surface text-ink'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap break-words text-[15px] leading-relaxed">{message.text}</p>
          ) : (
            <>
              {isError ? (
                <p className="flex items-start gap-2 text-sm leading-relaxed">
                  <span className="mt-0.5 flex-none">
                    <AlertIcon />
                  </span>
                  <span>{message.text}</span>
                </p>
              ) : (
                <Suspense
                  fallback={
                    <p className="text-sm text-ink-faint">Preparando la respuesta…</p>
                  }
                >
                  <MarkdownRenderer markdown={message.text} />
                </Suspense>
              )}
            </>
          )}
        </div>

        <div className="flex items-center gap-2 px-1 text-xs text-ink-faint">
          <span>{isUser ? UI_TEXT.you : UI_TEXT.agent}</span>
          <span aria-hidden="true">·</span>
          <time dateTime={new Date(message.createdAt).toISOString()}>{time}</time>
          {!isUser && message.text ? <CopyButton text={message.text} /> : null}
        </div>

        {isUser && isLatest ? <span className="sr-only">Ultimo mensaje enviado</span> : null}
      </div>
    </article>
  );
};

export default MessageBubble;