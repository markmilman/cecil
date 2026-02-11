/**
 * ThemeToggle component
 *
 * Button that toggles between light and dark themes with
 * hover/focus state management and accessible labeling.
 */

import { MoonIcon, SunIcon } from 'lucide-react';
import { useThemeContext } from '@/hooks/useTheme';

export function ThemeToggle() {
  const { theme, toggleTheme } = useThemeContext();

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="flex cursor-pointer items-center justify-center rounded-full border-none bg-transparent p-2 transition-colors duration-200"
      style={{ color: 'var(--text-secondary)' }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = 'var(--bg-body)';
        e.currentTarget.style.color = 'var(--text-primary)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = 'transparent';
        e.currentTarget.style.color = 'var(--text-secondary)';
      }}
      onFocus={(e) => {
        e.currentTarget.style.backgroundColor = 'var(--bg-body)';
        e.currentTarget.style.color = 'var(--text-primary)';
      }}
      onBlur={(e) => {
        e.currentTarget.style.backgroundColor = 'transparent';
        e.currentTarget.style.color = 'var(--text-secondary)';
      }}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
      title="Toggle Theme"
    >
      {theme === 'light' ? (
        <MoonIcon className="h-5 w-5" />
      ) : (
        <SunIcon className="h-5 w-5" />
      )}
    </button>
  );
}
