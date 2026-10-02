import type { ReactNode } from 'react';

interface IconProps {
  readonly className?: string;
}

/**
 * Iconos en SVG inline para no depender de una libreria externa.
 * `aria-hidden` porque el texto que los acompaña ya aporta el significado.
 */
function Base({ children, className = '' }: IconProps & { readonly children: ReactNode }) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      viewBox="0 0 24 24"
    >
      {children}
    </svg>
  );
}

export function SendIcon({ className = 'size-5' }: IconProps) {
  return (
    <Base className={className}>
      <path d="M4.5 12h13" />
      <path d="m12 6 6 6-6 6" />
    </Base>
  );
}

export function StopIcon({ className = 'size-5' }: IconProps) {
  return (
    <Base className={className}>
      <rect height="11" rx="2" width="11" x="6.5" y="6.5" />
    </Base>
  );
}

export function CopyIcon({ className = 'size-4' }: IconProps) {
  return (
    <Base className={className}>
      <rect height="11" rx="2" width="11" x="9" y="9" />
      <path d="M15 5.5V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h.5" />
    </Base>
  );
}

export function CheckIcon({ className = 'size-4' }: IconProps) {
  return (
    <Base className={className}>
      <path d="m5 12.5 4.5 4.5L19 7" />
    </Base>
  );
}

export function SunIcon({ className = 'size-5' }: IconProps) {
  return (
    <Base className={className}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </Base>
  );
}

export function MoonIcon({ className = 'size-5' }: IconProps) {
  return (
    <Base className={className}>
      <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z" />
    </Base>
  );
}

export function SparkIcon({ className = 'size-5' }: IconProps) {
  return (
    <Base className={className}>
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4M6.3 6.3l2.4 2.4M15.3 15.3l2.4 2.4M17.7 6.3l-2.4 2.4M8.7 15.3l-2.4 2.4" />
    </Base>
  );
}

export function AlertIcon({ className = 'size-4' }: IconProps) {
  return (
    <Base className={className}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7.5v5.5M12 16.4h.01" />
    </Base>
  );
}

export function RefreshIcon({ className = 'size-5' }: IconProps) {
  return (
    <Base className={className}>
      <path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3" />
      <path d="M19.5 4v4h-4" />
    </Base>
  );
}