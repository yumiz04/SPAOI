import { useCallback, useEffect, useRef, useState } from 'react';
import type { FC } from 'react';
import { CheckIcon, CopyIcon } from '../icons';
import { UI_TEXT } from '../../data/mockData';

interface CopyButtonProps {
  readonly text: string;
}

/** Copia la respuesta al portapapeles y confirma el estado durante 1.6 s. */
export const CopyButton: FC<CopyButtonProps> = ({ text }) => {
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  }, []);

  const handleClick = useCallback(() => {
    const write = navigator.clipboard?.writeText(text);
    if (!write) {
      return;
    }
    void write.then(() => {
      setCopied(true);
      timeoutRef.current = setTimeout(() => setCopied(false), 1600);
    });
  }, [text]);

  return (
    <button
      aria-label={copied ? UI_TEXT.copied : UI_TEXT.copy}
      className="inline-flex size-7 items-center justify-center rounded-md text-ink-faint transition-colors hover:bg-surface-3 hover:text-ink"
      onClick={handleClick}
      title={copied ? UI_TEXT.copied : UI_TEXT.copy}
      type="button"
    >
      {copied ? <CheckIcon className="size-4 text-ok" /> : <CopyIcon />}
    </button>
  );
};

export default CopyButton;