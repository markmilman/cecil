import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { JobHistoryTable } from './JobHistoryTable';
import { ScanStatus } from '@/types';

import type { JobRecord } from '@/types';

const MOCK_JOBS: JobRecord[] = [
  {
    job_id: 'abc12345-6789-0000-0000-000000000001',
    status: ScanStatus.COMPLETED,
    source: '/data/aws-prod-logs.jsonl',
    source_format: 'jsonl',
    mapping_id: 'm1',
    mapping_name: 'Default',
    output_path: '/out/sanitized.jsonl',
    records_processed: 1420,
    records_sanitized: 1389,
    records_failed: 0,
    errors: [],
    created_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
  },
  {
    job_id: 'def12345-6789-0000-0000-000000000002',
    status: ScanStatus.FAILED,
    source: '/data/user-db-dump.csv',
    source_format: 'csv',
    mapping_id: null,
    mapping_name: null,
    output_path: '/out/sanitized2.csv',
    records_processed: 500,
    records_sanitized: 200,
    records_failed: 3,
    errors: ['Parse error on row 501'],
    created_at: new Date(Date.now() - 86_400_000).toISOString(),
    completed_at: null,
  },
];

const noop = vi.fn();
const noopJobClick = vi.fn();

describe('JobHistoryTable', () => {
  it('renders the table header columns', () => {
    render(<JobHistoryTable jobs={MOCK_JOBS} isLoading={false} error={null} onDeleteJob={noop} onJobClick={noopJobClick} />);
    expect(screen.getByText('Job ID')).toBeInTheDocument();
    expect(screen.getByText('Source')).toBeInTheDocument();
    expect(screen.getByText('Date')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Records')).toBeInTheDocument();
    expect(screen.getByText('Actions')).toBeInTheDocument();
  });

  it('renders source filenames extracted from paths', () => {
    render(<JobHistoryTable jobs={MOCK_JOBS} isLoading={false} error={null} onDeleteJob={noop} onJobClick={noopJobClick} />);
    expect(screen.getByText('aws-prod-logs.jsonl')).toBeInTheDocument();
    expect(screen.getByText('user-db-dump.csv')).toBeInTheDocument();
  });

  it('renders status pills with correct labels', () => {
    render(<JobHistoryTable jobs={MOCK_JOBS} isLoading={false} error={null} onDeleteJob={noop} onJobClick={noopJobClick} />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('renders loading state', () => {
    render(<JobHistoryTable jobs={[]} isLoading={true} error={null} onDeleteJob={noop} onJobClick={noopJobClick} />);
    expect(screen.getByText('Loading jobs...')).toBeInTheDocument();
  });

  it('renders empty state when no jobs', () => {
    render(<JobHistoryTable jobs={[]} isLoading={false} error={null} onDeleteJob={noop} onJobClick={noopJobClick} />);
    expect(screen.getByText(/No sanitization jobs yet/)).toBeInTheDocument();
  });

  it('renders error banner', () => {
    render(<JobHistoryTable jobs={[]} isLoading={false} error="Failed to load" onDeleteJob={noop} onJobClick={noopJobClick} />);
    expect(screen.getByText('Failed to load')).toBeInTheDocument();
  });

  it('calls onDeleteJob when delete button is clicked', () => {
    const onDelete = vi.fn();
    render(<JobHistoryTable jobs={MOCK_JOBS} isLoading={false} error={null} onDeleteJob={onDelete} onJobClick={noopJobClick} />);
    const deleteButtons = screen.getAllByTitle('Delete job');
    fireEvent.click(deleteButtons[0]);
    expect(onDelete).toHaveBeenCalledWith(MOCK_JOBS[0].job_id);
  });

  it('calls onJobClick when a row is clicked', () => {
    const onJobClick = vi.fn();
    render(<JobHistoryTable jobs={MOCK_JOBS} isLoading={false} error={null} onDeleteJob={noop} onJobClick={onJobClick} />);
    fireEvent.click(screen.getByText('aws-prod-logs.jsonl'));
    expect(onJobClick).toHaveBeenCalledWith(MOCK_JOBS[0]);
  });

  it('does not call onJobClick when delete button is clicked', () => {
    const onJobClick = vi.fn();
    const onDelete = vi.fn();
    render(<JobHistoryTable jobs={MOCK_JOBS} isLoading={false} error={null} onDeleteJob={onDelete} onJobClick={onJobClick} />);
    const deleteButtons = screen.getAllByTitle('Delete job');
    fireEvent.click(deleteButtons[0]);
    expect(onDelete).toHaveBeenCalledWith(MOCK_JOBS[0].job_id);
    expect(onJobClick).not.toHaveBeenCalled();
  });

  it('renders with correct grid column layout', () => {
    const { container } = render(
      <JobHistoryTable jobs={MOCK_JOBS} isLoading={false} error={null} onDeleteJob={noop} onJobClick={noopJobClick} />,
    );
    const header = container.querySelector('[style*="text-transform"]') as HTMLElement;
    expect(header.style.gridTemplateColumns).toBe('1.5fr 2fr 2fr 1.5fr 1fr 0.5fr');
  });
});
