import type { FC } from 'react';
import { AppShell } from '../layout/AppShell';
import { BrandBar } from '../layout/BrandBar';
import { Composer } from './Composer';
import { MessageList } from './MessageList';
import { SuggestionChips } from './SuggestionChips';
import { APP_META, SUGGESTION_PROMPTS, UI_TEXT } from '../../data/mockData';
import { useAgentHealth } from '../../hooks/useAgentHealth';
import { useChat } from '../../hooks/useChat';
import { useTheme } from '../../hooks/useTheme';

interface ChatViewProps {
  /** La vista no recibe propiedades: su estado vive en `useChat` y `useTheme`. */
  readonly className?: string;
}

/** Pantalla principal: conversacion con el agente de inventario. */
export const ChatView: FC<ChatViewProps> = () => {
  const { theme, toggleTheme } = useTheme();
  const { messages, sessionId, isThinking, send, stop, startNewConversation } = useChat();
  const { isReachable } = useAgentHealth();

  const isEmpty = messages.length === 0;

  return (
    <AppShell
      header={
        <BrandBar
          onNewConversation={startNewConversation}
          onToggleTheme={toggleTheme}
          sessionId={sessionId}
          theme={theme}
        />
      }
    >
      {isReachable === false ? (
        <div
          className="border-b border-danger/30 bg-danger-soft px-4 py-2 text-center text-sm text-ink sm:px-6"
          role="status"
        >
          {UI_TEXT.agentOffline}
        </div>
      ) : null}

      <MessageList isThinking={isThinking} messages={messages} />

      {isEmpty ? (
        <div className="mx-auto w-full max-w-4xl px-4 pb-6 sm:px-6">
          <div className="mb-5 text-center">
            <h1 className="text-xl font-semibold tracking-tight text-ink">{UI_TEXT.emptyTitle}</h1>
            <p className="mx-auto mt-1.5 max-w-xl text-sm text-ink-faint">{UI_TEXT.emptyHint}</p>
          </div>
          <SuggestionChips disabled={isThinking} onSelect={send} suggestions={SUGGESTION_PROMPTS} />
          <p className="mt-6 text-center text-xs text-ink-faint">{UI_TEXT.disclaimer}</p>
        </div>
      ) : null}

      <Composer isThinking={isThinking} onSend={send} onStop={stop} />

      {isEmpty ? (
        <p className="sr-only">{APP_META.source}</p>
      ) : null}
    </AppShell>
  );
};

export default ChatView;