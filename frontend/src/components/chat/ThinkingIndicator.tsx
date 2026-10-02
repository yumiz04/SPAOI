import { useEffect, useState } from 'react';
import type { FC } from 'react';
import { SparkIcon } from '../icons';
import { UI_TEXT } from '../../data/mockData';

interface ThinkingIndicatorProps {
  readonly isThinking: boolean;
}

/** Aviso de "el agente esta consultando" con los segundos transcurridos. */
export const ThinkingIndicator: FC<ThinkingIndicatorProps> = ({ isThinking }) => {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!isThinking) {
      setElapsed(0);
      return;
    }

    const startedAt = Date.now();
    const tick = setInterval(() => setElapsed(Math.floor((Date.now() - startedAt) / 1000)), 1000);

    return () => clearInterval(tick);
  }, [isThinking]);

  if (!isThinking) {
    return null;
  }

  return (
    <div aria-live="polite" className="msg-auto flex w-full items-start gap-3">
      <div className="mt-1 flex size-8 flex-none items-center justify-center rounded-full bg-brand-soft text-brand">
        <SparkIcon className="size-4" />
      </div>
      <div className="flex flex-col gap-1.5 rounded-card border border-line bg-surface px-4 py-3 shadow-soft">
        <p className="flex items-center gap-2 text-sm font-medium text-ink">
          {UI_TEXT.thinking}
          <span className="flex items-center gap-1" aria-hidden="true">
            <span className="thinking-dot size-1.5 rounded-full bg-brand" />
            <span className="thinking-dot size-1.5 rounded-full bg-brand" />
            <span className="thinking-dot size-1.5 rounded-full bg-brand" />
          </span>
          <span className="tabular-nums text-ink-faint">{elapsed}s</span>
        </p>
        <p className="text-xs text-ink-faint">{UI_TEXT.thinkingHint}</p>
      </div>
    </div>
  );
};

export default ThinkingIndicator;