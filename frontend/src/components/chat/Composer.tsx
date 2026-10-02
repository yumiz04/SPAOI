import { useCallback, useRef, useState } from 'react';
import type { FC, FormEvent, KeyboardEvent } from 'react';
import { SendIcon, StopIcon } from '../icons';
import { UI_TEXT } from '../../data/mockData';

interface ComposerProps {
  readonly isThinking: boolean;
  readonly onSend: (text: string) => void;
  readonly onStop: () => void;
}

const MAX_TEXTAREA_HEIGHT = 200;

/** Caja de escritura: Enter envia, Shift+Enter hace salto de linea. */
export const Composer: FC<ComposerProps> = ({ isThinking, onSend, onStop }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const resize = useCallback(() => {
    const element = textareaRef.current;
    if (!element) {
      return;
    }
    element.style.height = 'auto';
    element.style.height = `${Math.min(element.scrollHeight, MAX_TEXTAREA_HEIGHT)}px`;
  }, []);

  const submit = useCallback(
    (event?: FormEvent) => {
      event?.preventDefault();
      const value = text.trim();
      if (!value || isThinking) {
        return;
      }
      onSend(value);
      setText('');
      requestAnimationFrame(resize);
    },
    [isThinking, onSend, resize, text],
  );

  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        submit();
      }
    },
    [submit],
  );

  const canSend = text.trim().length > 0 && !isThinking;

  return (
    <form
      className="border-t border-line bg-surface/80 px-4 py-3 backdrop-blur sm:px-6"
      onSubmit={submit}
    >
      <div className="mx-auto flex w-full max-w-4xl items-end gap-2 rounded-card border border-line bg-surface p-2 shadow-soft focus-within:border-brand/60">
        <label className="sr-only" htmlFor="composer">
          {UI_TEXT.composerLabel}
        </label>
        <textarea
          aria-label={UI_TEXT.composerLabel}
          className="max-h-[200px] min-h-[2.5rem] w-full resize-none bg-transparent px-2 py-2 text-[15px] leading-relaxed text-ink outline-none placeholder:text-ink-faint"
          id="composer"
          onChange={(event) => {
            setText(event.target.value);
            resize();
          }}
          onKeyDown={handleKeyDown}
          placeholder={UI_TEXT.composerPlaceholder}
          ref={textareaRef}
          rows={1}
          value={text}
        />

        {isThinking ? (
          <button
            aria-label={UI_TEXT.stop}
            className="flex size-10 flex-none items-center justify-center rounded-card border border-line text-ink-muted transition-colors hover:bg-surface-3 hover:text-ink"
            onClick={onStop}
            title={UI_TEXT.stop}
            type="button"
          >
            <StopIcon />
          </button>
        ) : (
          <button
            aria-label={UI_TEXT.send}
            className="flex size-10 flex-none items-center justify-center rounded-card bg-brand text-brand-ink transition-colors hover:bg-brand-strong disabled:cursor-not-allowed disabled:bg-surface-3 disabled:text-ink-faint"
            disabled={!canSend}
            title={UI_TEXT.send}
            type="submit"
          >
            <SendIcon />
          </button>
        )}
      </div>
    </form>
  );
};

export default Composer;