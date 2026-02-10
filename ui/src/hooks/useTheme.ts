import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

export type Theme = 'light' | 'dark';

const STORAGE_KEY = 'cecil-theme';

function getInitialTheme(): Theme {
  if (typeof window === 'undefined') {
    return 'light';
  }

  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'light' || stored === 'dark') {
    return stored;
  }

  return 'light';
}

export interface UseThemeReturn {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

/**
 * Internal React context. Consumers should use `useThemeContext()`
 * rather than importing the context directly.
 */
export const ThemeContext = createContext<UseThemeReturn | null>(null);

/**
 * Low-level hook that manages theme state, persists the preference
 * to localStorage, and sets the `data-theme` attribute on
 * `document.documentElement` so CSS custom properties resolve correctly.
 *
 * Most components should use `useThemeContext()` instead — this hook
 * is consumed by the `ThemeProvider` component.
 */
export function useTheme(): UseThemeReturn {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const setTheme = useCallback((next: Theme) => {
    setThemeState(next);
  }, []);

  const toggleTheme = useCallback(() => {
    setThemeState((prev) => (prev === 'light' ? 'dark' : 'light'));
  }, []);

  return useMemo(
    () => ({ theme, toggleTheme, setTheme }),
    [theme, toggleTheme, setTheme],
  );
}

/**
 * Consume the nearest `ThemeProvider` context. Throws if called
 * outside a provider so missing providers surface immediately
 * during development.
 */
export function useThemeContext(): UseThemeReturn {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('useThemeContext must be used within a ThemeProvider');
  }
  return ctx;
}
