import { StatCard } from './StatCard';

import type { JobRecord } from '@/types';

interface StatsGridProps {
  jobs: JobRecord[];
}

/**
 * 3-column stats grid for the dashboard.
 *
 * Derives real stats from job data: Records Processed, PII Sanitized
 * (with trend showing sanitized-to-processed ratio), and Total Jobs.
 */
export function StatsGrid({ jobs }: StatsGridProps) {
  const totalProcessed = jobs.reduce((sum, j) => sum + j.records_processed, 0);
  const totalSanitized = jobs.reduce((sum, j) => sum + j.records_sanitized, 0);
  const sanitizedPct = totalProcessed > 0
    ? ((totalSanitized / totalProcessed) * 100).toFixed(1)
    : '0.0';

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
        value={totalProcessed.toLocaleString()}
      />
      <StatCard
        label="PII Sanitized"
        value={totalSanitized.toLocaleString()}
        trend={{ label: `${sanitizedPct}%`, direction: 'up' }}
      />
      <StatCard
        label="Total Jobs"
        value={jobs.length.toLocaleString()}
        highlight
      />
    </div>
  );
}
