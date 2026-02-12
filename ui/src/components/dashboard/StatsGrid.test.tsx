import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatsGrid } from './StatsGrid';
import { ScanStatus } from '@/types';

import type { JobRecord } from '@/types';

function makeJob(overrides: Partial<JobRecord> = {}): JobRecord {
  return {
    job_id: 'job-001',
    status: ScanStatus.COMPLETED,
    source: '/data/test.jsonl',
    source_format: 'jsonl',
    mapping_id: null,
    mapping_name: null,
    output_path: '/out/test.jsonl',
    records_processed: 100,
    records_sanitized: 80,
    records_failed: 0,
    errors: [],
    created_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
    ...overrides,
  };
}

describe('StatsGrid', () => {
  it('renders three stat cards', () => {
    render(<StatsGrid jobs={[makeJob()]} />);
    expect(screen.getByText('Records Processed')).toBeInTheDocument();
    expect(screen.getByText('PII Sanitized')).toBeInTheDocument();
    expect(screen.getByText('Total Jobs')).toBeInTheDocument();
  });

  it('derives stats from job data', () => {
    const jobs = [
      makeJob({ records_processed: 1000, records_sanitized: 800 }),
      makeJob({ job_id: 'job-002', records_processed: 500, records_sanitized: 200 }),
    ];
    render(<StatsGrid jobs={jobs} />);
    expect(screen.getByText('1,500')).toBeInTheDocument();
    expect(screen.getByText('1,000')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('shows sanitized-to-processed ratio as trend', () => {
    const jobs = [makeJob({ records_processed: 1000, records_sanitized: 500 })];
    render(<StatsGrid jobs={jobs} />);
    expect(screen.getByText('50.0%')).toBeInTheDocument();
  });

  it('renders with a 3-column grid layout', () => {
    const { container } = render(<StatsGrid jobs={[]} />);
    const grid = container.firstChild as HTMLElement;
    expect(grid.style.gridTemplateColumns).toBe('repeat(3, 1fr)');
  });

  it('shows zeros when no jobs', () => {
    render(<StatsGrid jobs={[]} />);
    const zeros = screen.getAllByText('0');
    expect(zeros.length).toBeGreaterThanOrEqual(2);
  });
});
