type StatusVariant = 'success' | 'danger' | 'warning' | 'neutral';

interface StatusPillProps {
  label: string;
  variant: StatusVariant;
}

const VARIANT_STYLES: Record<StatusVariant, { backgroundColor: string; color: string }> = {
  success: {
    backgroundColor: 'var(--success-bg)',
    color: 'var(--success-color)',
  },
  danger: {
    backgroundColor: 'var(--danger-bg)',
    color: 'var(--danger-color)',
  },
  warning: {
    backgroundColor: 'var(--warning-bg)',
    color: 'var(--warning-color)',
  },
  neutral: {
    backgroundColor: '#f1f5f9',
    color: '#64748b',
  },
};

/**
 * Colored pill badge for status indicators.
 *
 * Supports "success" (green) and "danger" (red) variants, styled
 * with CSS custom properties for theme support.
 */
export function StatusPill({ label, variant }: StatusPillProps) {
  const styles = VARIANT_STYLES[variant];

  return (
    <span
      style={{
        display: 'inline-block',
        padding: '4px 12px',
        borderRadius: '99px',
        fontSize: '12px',
        fontWeight: 600,
        backgroundColor: styles.backgroundColor,
        color: styles.color,
      }}
    >
      {label}
    </span>
  );
}
