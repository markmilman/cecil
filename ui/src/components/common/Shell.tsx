import { type ReactNode } from 'react';
import { NavLink } from '@/components/common/NavLink';
import { ThemeToggle } from '@/components/common/ThemeToggle';

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
  enabled: boolean;
}

const NAV_LINKS: NavLinkItem[] = [
  { view: 'dashboard', label: 'Dashboard', enabled: true },
  { view: 'mapping', label: 'Mapping Rules', enabled: false },
  { view: 'settings', label: 'Settings', enabled: false },
];

/**
 * Shell layout component with top navigation bar
 *
 * Provides the main layout structure with a fixed 64px top nav bar
 * containing logo, navigation links, and theme toggle.
 * Navigation is state-driven via props rather than React Router.
 */
export function Shell({ children, activeView, onNavigate }: ShellProps) {
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
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.view}
                view={link.view}
                label={link.label}
                enabled={link.enabled}
                isActive={activeView === link.view}
                onClick={onNavigate}
              />
            ))}
          </div>
        </div>

        {/* Right: Theme Toggle */}
        <ThemeToggle />
      </nav>

      {/* Main Content Area */}
      <main id="main-content" className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
