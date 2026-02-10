import { StatusPill } from '@/components/common/StatusPill';

interface JobRow {
  id: string;
  source: string;
  date: string;
  status: 'completed' | 'pii_detected';
  actionLabel: string;
}

const MOCK_JOBS: JobRow[] = [
  {
    id: 'local-job-003',
    source: 'aws-prod-logs.jsonl',
    date: 'Today, 10:42 AM',
    status: 'completed',
    actionLabel: 'View Report',
  },
  {
    id: 'local-job-002',
    source: 'user-db-dump.csv',
    date: 'Yesterday, 4:15 PM',
    status: 'pii_detected',
    actionLabel: 'Review',
  },
];

const GRID_COLUMNS = '2fr 2fr 2fr 1fr 1fr';

/**
 * Job history table for the dashboard.
 *
 * Renders a card-wrapped table with a 5-column CSS grid layout:
 * Job ID, Source, Date, Status (pill), and Action (button).
 * Uses static mock data.
 */
export function JobHistoryTable() {
  return (
    <div
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px 24px',
          backgroundColor: 'var(--bg-body)',
          borderBottom: '1px solid var(--border-color)',
          display: 'grid',
          gridTemplateColumns: GRID_COLUMNS,
          fontSize: '12px',
          fontWeight: 600,
          color: 'var(--text-secondary)',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        }}
      >
        <div>Job ID</div>
        <div>Source</div>
        <div>Date</div>
        <div>Status</div>
        <div>Action</div>
      </div>

      {/* Rows */}
      {MOCK_JOBS.map((job) => (
        <div
          key={job.id}
          style={{
            padding: '16px 24px',
            borderBottom: '1px solid var(--border-color)',
            display: 'grid',
            gridTemplateColumns: GRID_COLUMNS,
            alignItems: 'center',
            fontSize: '14px',
            transition: 'background-color 0.1s',
            color: 'var(--text-primary)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'var(--bg-body)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
          }}
        >
          <div style={{ fontFamily: 'monospace' }}>{job.id}</div>
          <div>{job.source}</div>
          <div>{job.date}</div>
          <div>
            <StatusPill
              label={job.status === 'completed' ? 'Completed' : 'PII Detected'}
              variant={job.status === 'completed' ? 'success' : 'danger'}
            />
          </div>
          <div>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ padding: '4px 12px', fontSize: '12px' }}
            >
              {job.actionLabel}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
