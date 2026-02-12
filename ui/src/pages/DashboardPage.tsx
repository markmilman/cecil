import { useState, useEffect } from 'react';
import { StatsGrid } from '@/components/dashboard/StatsGrid';
import { JobHistoryTable } from '@/components/dashboard/JobHistoryTable';
import { JobDetailDrawer } from '@/components/dashboard/JobDetailDrawer';
import { useJobList } from '@/hooks/useJobList';

import type { JobRecord } from '@/types';

const POLL_INTERVAL_MS = 10_000;

interface DashboardPageProps {
  onStartWizard: () => void;
  onViewMapping?: (mappingId: string) => void;
}

/**
 * Dashboard page showing the audit overview.
 *
 * Displays a page header with title/subtitle and a "+ New Sanitization
 * Job" primary button, followed by the stats grid and job history table.
 * Fetches real job data via the useJobList hook with 10-second polling.
 */
export function DashboardPage({ onStartWizard, onViewMapping }: DashboardPageProps) {
  const { jobs, isLoading, error, refresh, deleteJobById } = useJobList();
  const [selectedJob, setSelectedJob] = useState<JobRecord | null>(null);

  useEffect(() => {
    const id = setInterval(() => {
      refresh();
    }, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [refresh]);

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

      <StatsGrid jobs={jobs} />

      <JobHistoryTable
        jobs={jobs}
        isLoading={isLoading}
        error={error}
        onDeleteJob={deleteJobById}
        onJobClick={setSelectedJob}
      />

      <JobDetailDrawer
        job={selectedJob}
        onClose={() => setSelectedJob(null)}
        onViewMapping={onViewMapping ? (mappingId) => {
          setSelectedJob(null);
          onViewMapping(mappingId);
        } : undefined}
      />
    </div>
  );
}
