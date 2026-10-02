import type { FC } from 'react';
import { Link } from 'react-router-dom';
import { MoonIcon, RefreshIcon, SunIcon } from '../icons';
import { APP_META, UI_TEXT } from '../../data/mockData';
import type { Theme } from '../../types/chat';

interface BrandBarProps {
  readonly sessionId: string;
  readonly theme: Theme;
  readonly onNewConversation: () => void;
  readonly onToggleTheme: () => void;
}

const SESSION_PREVIEW_LENGTH = 8;

/** Barra superior: marca (enlazada al inicio), sesion vigente y acciones. */
export const BrandBar: FC<BrandBarProps> = ({ sessionId, theme, onNewConversation, onToggleTheme }) => {
  const sessionPreview = sessionId.length > SESSION_PREVIEW_LENGTH ? sessionId.slice(-SESSION_PREVIEW_LENGTH) : sessionId;

  return (
    <header className="border-b border-line bg-surface/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-4xl items-center gap-3 px-4 py-3 sm:px-6">
        <Link
          className="flex min-w-0 items-center gap-3 rounded-card px-1 py-1 transition-opacity hover:opacity-80"
          to="/"
        >
          <span className="flex size-9 flex-none items-center justify-center rounded-card bg-brand text-sm font-bold text-brand-ink">
            AI
          </span>
          <span className="flex min-w-0 flex-col">
            <span className="truncate text-sm font-semibold text-ink">{APP_META.name}</span>
            <span className="truncate text-xs text-ink-faint">{APP_META.tagline}</span>
          </span>
        </Link>

        <span
          className="ml-auto hidden font-mono text-xs text-ink-faint sm:inline"
          title={`${UI_TEXT.sessionLabel}: ${sessionId}`}
        >
          {UI_TEXT.sessionLabel} · {sessionPreview}
        </span>

        <button
          className="flex size-9 flex-none items-center justify-center rounded-card border border-line text-ink-muted transition-colors hover:bg-surface-3 hover:text-ink"
          onClick={onNewConversation}
          title={UI_TEXT.newConversation}
          type="button"
        >
          <RefreshIcon />
          <span className="sr-only">{UI_TEXT.newConversation}</span>
        </button>

        <button
          className="flex size-9 flex-none items-center justify-center rounded-card border border-line text-ink-muted transition-colors hover:bg-surface-3 hover:text-ink"
          onClick={onToggleTheme}
          title={UI_TEXT.themeToggle}
          type="button"
        >
          {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
          <span className="sr-only">{UI_TEXT.themeToggle}</span>
        </button>
      </div>
    </header>
  );
};

export default BrandBar;