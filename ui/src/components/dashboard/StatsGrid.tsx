import { StatCard } from './StatCard';

/**
 * 3-column stats grid for the dashboard.
 *
 * Displays static mock data: Records Processed, PII Redacted (with
 * trend pill), and Est. Cost Savings (highlighted with primary colors).
 */
export function StatsGrid() {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '24px',
        marginBottom: '32px',
      }}
    >
      <StatCard
        label="Records Processed"
        value="14,205"
      />
      <StatCard
        label="PII Redacted"
        value="1,892"
        trend={{ label: '13.2%', direction: 'up' }}
      />
      <StatCard
        label="Est. Cost Savings"
        value={
          <>
            $4,200<span style={{ fontSize: '16px' }}>/mo</span>
          </>
        }
        highlight
      />
    </div>
  );
}
