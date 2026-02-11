/**
 * NavLink component
 *
 * Individual navigation link button with hover/focus state management
 * and support for disabled "Coming soon" links.
 */

interface NavLinkProps {
  view: string;
  label: string;
  enabled: boolean;
  isActive: boolean;
  onClick: (view: string) => void;
}

export function NavLink({ view, label, enabled, isActive, onClick }: NavLinkProps) {
  return (
    <button
      type="button"
      role="listitem"
      onClick={() => enabled && onClick(view)}
      disabled={!enabled}
      className="border-none bg-transparent text-sm font-medium transition-colors duration-200"
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
    </button>
  );
}
