import { StatsGrid } from '@/components/dashboard/StatsGrid';
import { JobHistoryTable } from '@/components/dashboard/JobHistoryTable';

interface DashboardPageProps {
  onStartWizard: () => void;
}

/**
 * Dashboard page showing the audit overview.
 *
 * Displays a page header with title/subtitle and a "+ New Sanitization
 * Job" primary button, followed by the stats grid and job history table.
 */
export function DashboardPage({ onStartWizard }: DashboardPageProps) {
  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '24px',
        }}
      >
        <div>
          <h2
            style={{
              margin: 0,
              fontSize: '24px',
              color: 'var(--text-primary)',
            }}
          >
            Audit Dashboard
          </h2>
          <p
            style={{
              margin: '4px 0 0',
              color: 'var(--text-secondary)',
              fontSize: '14px',
            }}
          >
            Overview of recent sanitization jobs and PII detection.
          </p>
        </div>
        <button
          type="button"
          className="btn btn-primary"
          onClick={onStartWizard}
        >
          <span style={{ fontSize: '18px' }}>+</span> New Sanitization Job
        </button>
      </div>

      <StatsGrid />

      <JobHistoryTable />
    </div>
  );
}
