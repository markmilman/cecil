import type { ReactNode } from 'react';

interface TrendPill {
  label: string;
  direction: 'up' | 'down';
}

interface StatCardProps {
  label: string;
  value: ReactNode;
  trend?: TrendPill;
  highlight?: boolean;
}

/**
 * Individual stat card for the dashboard stats grid.
 *
 * Displays a metric label and value. Optionally shows a trend pill
 * (e.g. "+13.2%") and can be highlighted with primary/accent colors
 * for the cost savings card.
 */
export function StatCard({ label, value, trend, highlight }: StatCardProps) {
  return (
    <div
      style={{
        backgroundColor: highlight ? 'var(--primary-light)' : 'var(--bg-card)',
        border: `1px solid ${highlight ? 'var(--primary-color)' : 'var(--border-color)'}`,
        borderRadius: '12px',
        padding: '24px',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <div
        style={{
          fontSize: '13px',
          fontWeight: 500,
          color: highlight ? 'var(--primary-color)' : 'var(--text-secondary)',
          marginBottom: '8px',
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: '32px',
          fontWeight: 700,
          color: highlight ? 'var(--primary-color)' : 'var(--text-primary)',
        }}
      >
        {value}
        {trend && (
          <span
            style={{
              display: 'inline-block',
              padding: '2px 8px',
              borderRadius: '99px',
              fontSize: '12px',
              fontWeight: 600,
              marginLeft: '8px',
              verticalAlign: 'middle',
              backgroundColor: trend.direction === 'up'
                ? 'var(--success-bg)'
                : 'var(--danger-bg)',
              color: trend.direction === 'up'
                ? 'var(--success-color)'
                : 'var(--danger-color)',
            }}
          >
            {trend.label}
          </span>
        )}
      </div>
    </div>
  );
}
