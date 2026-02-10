import { useTheme, ThemeContext } from '@/hooks/useTheme';

import type { ReactNode } from 'react';

interface ThemeProviderProps {
  children: ReactNode;
}

/**
 * Provides the current theme and toggle/set functions to the React
 * component tree via context. Wrap the application root with this
 * provider so any descendant can call `useThemeContext()`.
 */
export function ThemeProvider({ children }: ThemeProviderProps) {
  const themeValue = useTheme();

  return (
    <ThemeContext.Provider value={themeValue}>
      {children}
    </ThemeContext.Provider>
  );
}
