import type { MouseEvent } from 'react';

/**
 * NavLink component
 *
 * Individual navigation link rendered as an <a> tag with href for
 * proper URL-based routing. Click handler prevents default and
 * delegates to the onNavigate callback.
 */

interface NavLinkProps {
  view: string;
  label: string;
  href: string;
  enabled: boolean;
  isActive: boolean;
  onClick: (view: string) => void;
}

export function NavLink({ view, label, href, enabled, isActive, onClick }: NavLinkProps) {
  const handleClick = (e: MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    if (enabled) {
      onClick(view);
    }
  };

  return (
    <a
      href={href}
      role="listitem"
      onClick={handleClick}
      aria-disabled={!enabled || undefined}
      className="border-none bg-transparent text-sm font-medium no-underline transition-colors duration-200"
      style={{
        color: !enabled
          ? 'var(--text-faint)'
          : isActive
            ? 'var(--text-primary)'
            : 'var(--text-secondary)',
        padding: 0,
        cursor: enabled ? 'pointer' : 'default',
      }}
      onMouseEnter={(e) => {
        if (enabled && !isActive) {
          e.currentTarget.style.color = 'var(--primary-color)';
        }
      }}
      onMouseLeave={(e) => {
        if (!enabled) return;
        e.currentTarget.style.color = isActive
          ? 'var(--text-primary)'
          : 'var(--text-secondary)';
      }}
      onFocus={(e) => {
        if (enabled && !isActive) {
          e.currentTarget.style.color = 'var(--primary-color)';
        }
      }}
      onBlur={(e) => {
        if (!enabled) return;
        e.currentTarget.style.color = isActive
          ? 'var(--text-primary)'
          : 'var(--text-secondary)';
      }}
      aria-current={isActive ? 'page' : undefined}
      title={!enabled ? 'Coming soon' : undefined}
    >
      {label}
    </a>
  );
}
