import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from './ThemeProvider';
import { useThemeContext } from '@/hooks/useTheme';

function ThemeConsumer() {
  const { theme, toggleTheme } = useThemeContext();
  return (
    <div>
      <span data-testid="theme-value">{theme}</span>
      <button onClick={toggleTheme}>Toggle</button>
    </div>
  );
}

describe('ThemeProvider', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
  });

  it('provides theme context to children', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    expect(screen.getByTestId('theme-value')).toHaveTextContent('light');
  });

  it('allows toggling theme via context', () => {
    render(
      <ThemeProvider>
        <ThemeConsumer />
      </ThemeProvider>,
    );
    fireEvent.click(screen.getByText('Toggle'));
    expect(screen.getByTestId('theme-value')).toHaveTextContent('dark');
  });

  it('throws when useThemeContext is used outside provider', () => {
    expect(() => {
      render(<ThemeConsumer />);
    }).toThrow('useThemeContext must be used within a ThemeProvider');
  });
});
