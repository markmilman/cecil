import { Trash2 } from 'lucide-react';
import { StatusPill } from '@/components/common/StatusPill';

import type { JobRecord } from '@/types';

interface JobHistoryTableProps {
  jobs: JobRecord[];
  isLoading: boolean;
  error: string | null;
  onDeleteJob: (jobId: string) => void;
  onJobClick: (job: JobRecord) => void;
}

const GRID_COLUMNS = '1.5fr 2fr 2fr 1.5fr 1fr 0.5fr';

/**
 * Format a date string as relative: "Today, HH:MM", "Yesterday, HH:MM",
 * or "MMM DD, YYYY".
 */
function formatDate(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 86_400_000);
  const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());

  const time = date.toLocaleTimeString(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  });

  if (dateOnly.getTime() === today.getTime()) {
    return `Today, ${time}`;
  }
  if (dateOnly.getTime() === yesterday.getTime()) {
    return `Yesterday, ${time}`;
  }
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

/**
 * Map a job status to a StatusPill variant and label.
 */
function statusToPill(status: string): { label: string; variant: 'success' | 'danger' | 'warning' | 'neutral' } {
  switch (status) {
    case 'completed':
      return { label: 'Completed', variant: 'success' };
    case 'failed':
      return { label: 'Failed', variant: 'danger' };
    case 'running':
      return { label: 'Running', variant: 'warning' };
    case 'pending':
      return { label: 'Pending', variant: 'neutral' };
    case 'cancelled':
      return { label: 'Cancelled', variant: 'neutral' };
    default:
      return { label: status, variant: 'neutral' };
  }
}

/**
 * Format a number with commas (e.g. 1234 → "1,234").
 */
function formatNumber(n: number): string {
  return n.toLocaleString();
}

/**
 * Job history table for the dashboard.
 *
 * Renders a card-wrapped table with a 6-column CSS grid layout:
 * Job ID, Source, Date, Records, Status (pill), and Actions (delete).
 * Accepts real job data via props from the useJobList hook.
 */
export function JobHistoryTable({ jobs, isLoading, error, onDeleteJob, onJobClick }: JobHistoryTableProps) {
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
      {/* Error banner */}
      {error && (
        <div
          style={{
            padding: '12px 24px',
            backgroundColor: 'var(--danger-bg)',
            color: 'var(--danger-color)',
            fontSize: '13px',
            fontWeight: 500,
          }}
        >
          {error}
        </div>
      )}

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
        <div>Records</div>
        <div>Status</div>
        <div>Actions</div>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div
          style={{
            padding: '48px 24px',
            textAlign: 'center',
            color: 'var(--text-secondary)',
            fontSize: '14px',
          }}
        >
          Loading jobs...
        </div>
      )}

      {/* Empty state */}
      {!isLoading && jobs.length === 0 && (
        <div
          style={{
            padding: '48px 24px',
            textAlign: 'center',
            color: 'var(--text-secondary)',
            fontSize: '14px',
          }}
        >
          No sanitization jobs yet. Click &quot;+ New Sanitization Job&quot; to get started.
        </div>
      )}

      {/* Rows */}
      {!isLoading &&
        jobs.map((job) => {
          const pill = statusToPill(job.status);
          const filename = job.source.split('/').pop() ?? job.source;

          return (
            <div
              key={job.job_id}
              style={{
                padding: '16px 24px',
                borderBottom: '1px solid var(--border-color)',
                display: 'grid',
                gridTemplateColumns: GRID_COLUMNS,
                alignItems: 'center',
                fontSize: '14px',
                transition: 'background-color 0.1s',
                color: 'var(--text-primary)',
                cursor: 'pointer',
              }}
              onClick={() => onJobClick(job)}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = 'var(--bg-body)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              <div
                style={{ fontFamily: 'monospace', fontSize: '13px' }}
                title={job.job_id}
              >
                {job.job_id.slice(0, 8)}
              </div>
              <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {filename}
              </div>
              <div>{formatDate(job.created_at)}</div>
              <div>
                {formatNumber(job.records_processed)} / {formatNumber(job.records_sanitized)}
              </div>
              <div>
                <StatusPill label={pill.label} variant={pill.variant} />
              </div>
              <div>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{
                    padding: '4px 8px',
                    fontSize: '12px',
                    display: 'inline-flex',
                    alignItems: 'center',
                  }}
                  onClick={(e) => { e.stopPropagation(); onDeleteJob(job.job_id); }}
                  title="Delete job"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          );
        })}
    </div>
  );
}
