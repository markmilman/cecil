import { type ReactNode } from 'react';
import { MoonIcon, SunIcon } from 'lucide-react';
import { useThemeContext } from '@/hooks/useTheme';

/**
 * Props for the Shell component
 */
interface ShellProps {
  children: ReactNode;
  activeView: string;
  onNavigate: (view: string) => void;
}

/**
 * Navigation link definition
 */
interface NavLinkItem {
  view: string;
  label: string;
}

const NAV_LINKS: NavLinkItem[] = [
  { view: 'dashboard', label: 'Dashboard' },
  { view: 'mapping', label: 'Mapping Rules' },
  { view: 'settings', label: 'Settings' },
];

/**
 * Shell layout component with top navigation bar
 *
 * Provides the main layout structure with a fixed 64px top nav bar
 * containing logo, navigation links, theme toggle, and user avatar.
 * Navigation is state-driven via props rather than React Router.
 */
export function Shell({ children, activeView, onNavigate }: ShellProps) {
  const { theme, toggleTheme } = useThemeContext();

  return (
    <div
      className="flex h-full flex-col"
      style={{ backgroundColor: 'var(--bg-body)' }}
    >
      {/* Skip Navigation Link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:shadow-lg"
        style={{
          backgroundColor: 'var(--bg-card)',
          color: 'var(--primary-color)',
        }}
      >
        Skip to main content
      </a>

      {/* Top Navigation Bar */}
      <nav
        aria-label="Main navigation"
        className="flex h-16 shrink-0 items-center justify-between px-6"
        style={{
          backgroundColor: 'var(--bg-nav)',
          borderBottom: '1px solid var(--border-color)',
          boxShadow: 'var(--shadow-sm)',
          zIndex: 10,
          transition: 'background-color 0.3s, border-color 0.3s',
        }}
      >
        {/* Left: Logo + Nav Links */}
        <div className="flex items-center gap-8">
          {/* Logo */}
          <div
            className="flex items-center gap-2 text-xl font-bold"
            style={{ color: 'var(--text-primary)' }}
          >
            <div
              className="h-6 w-6 rounded-md"
              style={{ backgroundColor: 'var(--primary-color)' }}
              aria-hidden="true"
            />
            Cecil
          </div>

          {/* Nav Links */}
          <div className="flex items-center gap-6" role="list">
            {NAV_LINKS.map((link) => {
              const isActive = activeView === link.view;
              return (
                <button
                  key={link.view}
                  type="button"
                  role="listitem"
                  onClick={() => onNavigate(link.view)}
                  className="cursor-pointer border-none bg-transparent text-sm font-medium transition-colors duration-200"
                  style={{
                    color: isActive
                      ? 'var(--text-primary)'
                      : 'var(--text-secondary)',
                    padding: 0,
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.color = 'var(--primary-color)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = isActive
                      ? 'var(--text-primary)'
                      : 'var(--text-secondary)';
                  }}
                  aria-current={isActive ? 'page' : undefined}
                >
                  {link.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Right: Theme Toggle + User Avatar */}
        <div className="flex items-center gap-4">
          {/* Theme Toggle */}
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
            aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
            title="Toggle Theme"
          >
            {theme === 'light' ? (
              <MoonIcon className="h-5 w-5" />
            ) : (
              <SunIcon className="h-5 w-5" />
            )}
          </button>

          {/* User Avatar */}
          <div
            className="flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold"
            style={{
              backgroundColor: 'var(--primary-light)',
              color: 'var(--primary-color)',
            }}
            aria-label="User avatar"
          >
            JS
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main id="main-content" className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
