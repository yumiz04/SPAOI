import { useCallback, useEffect, useState } from 'react';
import type { Theme } from '../types/chat';

const STORAGE_KEY = 'agente-inventario.theme';

function readInitialTheme(): Theme {
  if (typeof window === 'undefined') {
    return 'light';
  }

  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === 'dark' || stored === 'light') {
    return stored;
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export interface UseThemeResult {
  readonly theme: Theme;
  readonly toggleTheme: () => void;
}

/** Sincroniza el atributo `dark` del documento con el estado del tema. */
export function useTheme(): UseThemeResult {
  const [theme, setTheme] = useState<Theme>(readInitialTheme);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  const toggleTheme = useCallback(() => {
    setTheme((current) => {
      const next: Theme = current === 'dark' ? 'light' : 'dark';
      window.localStorage.setItem(STORAGE_KEY, next);
      return next;
    });
  }, []);

  return { theme, toggleTheme };
}