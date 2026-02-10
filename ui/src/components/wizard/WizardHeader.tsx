import type { ReactNode } from 'react';

/**
 * Props for the WizardHeader component
 */
interface WizardHeaderProps {
  title: string;
  subtitle: string;
  action?: ReactNode;
}

/**
 * WizardHeader component
 *
 * Reusable page header for wizard steps with title, subtitle,
 * and an optional right-side action slot (e.g., TrustBadge or a button).
 */
export function WizardHeader({ title, subtitle, action }: WizardHeaderProps) {
  return (
    <div
      className="flex items-center justify-between"
      style={{ marginBottom: '24px' }}
    >
      <div>
        <h2
          style={{
            margin: 0,
            fontSize: '24px',
            color: 'var(--text-primary)',
          }}
        >
          {title}
        </h2>
        <p
          style={{
            margin: '4px 0 0',
            color: 'var(--text-secondary)',
            fontSize: '14px',
          }}
        >
          {subtitle}
        </p>
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
