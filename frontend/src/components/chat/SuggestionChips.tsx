import type { FC } from 'react';
import type { SuggestionPrompt } from '../../data/mockData';

interface SuggestionChipsProps {
  readonly suggestions: readonly SuggestionPrompt[];
  readonly disabled: boolean;
  readonly onSelect: (prompt: string) => void;
}

/** Atajos de arranque cuando aun no hay conversacion. */
export const SuggestionChips: FC<SuggestionChipsProps> = ({ suggestions, disabled, onSelect }) => {
  return (
    <div className="flex flex-wrap justify-center gap-2">
      {suggestions.map((suggestion) => (
        <button
          className="rounded-full border border-line bg-surface px-3.5 py-1.5 text-sm text-ink-muted shadow-soft transition-colors hover:border-brand/50 hover:bg-brand-soft hover:text-brand disabled:cursor-not-allowed disabled:opacity-60"
          disabled={disabled}
          key={suggestion.id}
          onClick={() => onSelect(suggestion.prompt)}
          type="button"
        >
          {suggestion.label}
        </button>
      ))}
    </div>
  );
};

export default SuggestionChips;