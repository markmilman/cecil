import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DashboardPage } from './DashboardPage';
import { ScanStatus } from '@/types';

import type { JobRecord } from '@/types';

// Mock the apiClient
vi.mock('@/lib/apiClient', () => ({
  apiClient: {
    listJobs: vi.fn(),
    deleteJob: vi.fn(),
  },
}));

import { apiClient } from '@/lib/apiClient';

const MOCK_JOBS: JobRecord[] = [
  {
    job_id: 'aaaa1111-0000-0000-0000-000000000001',
    status: ScanStatus.COMPLETED,
    source: '/data/logs/api_calls.jsonl',
    source_format: 'jsonl',
    mapping_id: 'map-1',
    mapping_name: 'API Logs Mapping',
    output_path: '/output/api_calls_sanitized_aaaa1111.jsonl',
    records_processed: 5000,
    records_sanitized: 800,
    records_failed: 0,
    errors: [],
    created_at: '2026-01-15T10:00:00Z',
    completed_at: '2026-01-15T10:05:00Z',
  },
  {
    job_id: 'bbbb2222-0000-0000-0000-000000000002',
    status: ScanStatus.FAILED,
    source: '/data/exports/users.csv',
    source_format: 'csv',
    mapping_id: null,
    mapping_name: null,
    output_path: '/output/users_sanitized_bbbb2222.csv',
    records_processed: 3000,
    records_sanitized: 200,
    records_failed: 50,
    errors: ['Parse error on line 2501'],
    created_at: '2026-01-14T08:30:00Z',
    completed_at: '2026-01-14T08:32:00Z',
  },
  {
    job_id: 'cccc3333-0000-0000-0000-000000000003',
    status: ScanStatus.RUNNING,
    source: '/data/chat/messages.jsonl',
    source_format: 'jsonl',
    mapping_id: 'map-2',
    mapping_name: 'Chat Mapping',
    output_path: '/output/messages_sanitized_cccc3333.jsonl',
    records_processed: 2000,
    records_sanitized: 100,
    records_failed: 0,
    errors: [],
    created_at: '2026-01-16T14:00:00Z',
    completed_at: null,
  },
];

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.mocked(apiClient.listJobs).mockResolvedValue(MOCK_JOBS);
    vi.mocked(apiClient.deleteJob).mockResolvedValue(undefined);
  });

  it('renders the page heading', async () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    expect(screen.getByText('Audit Dashboard')).toBeInTheDocument();
  });

  it('renders the subtitle', async () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    expect(screen.getByText('Overview of recent sanitization jobs and PII detection.')).toBeInTheDocument();
  });

  it('renders the New Sanitization Job button', async () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    expect(screen.getByText('New Sanitization Job')).toBeInTheDocument();
  });

  it('calls onStartWizard when button is clicked', async () => {
    const onStartWizard = vi.fn();
    render(<DashboardPage onStartWizard={onStartWizard} />);
    fireEvent.click(screen.getByText('New Sanitization Job'));
    expect(onStartWizard).toHaveBeenCalledOnce();
  });

  it('renders the Records Processed stat', async () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText('Records Processed')).toBeInTheDocument();
      // 5000 + 3000 + 2000 = 10,000
      expect(screen.getByText('10,000')).toBeInTheDocument();
    });
  });

  it('renders the PII Sanitized stat with trend pill', async () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText('PII Sanitized')).toBeInTheDocument();
      // 800 + 200 + 100 = 1,100
      expect(screen.getByText('1,100')).toBeInTheDocument();
      // 1100 / 10000 * 100 = 11.0%
      expect(screen.getByText('11.0%')).toBeInTheDocument();
    });
  });

  it('renders the Total Jobs stat', async () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText('Total Jobs')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });
  });

  it('renders the job history table header', async () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    expect(screen.getByText('Job ID')).toBeInTheDocument();
    expect(screen.getByText('Source')).toBeInTheDocument();
    expect(screen.getByText('Date')).toBeInTheDocument();
    expect(screen.getByText('Records')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Actions')).toBeInTheDocument();
  });

  it('renders job history rows with status pills', async () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    await waitFor(() => {
      // Job IDs are displayed as first 8 chars
      expect(screen.getByText('aaaa1111')).toBeInTheDocument();
      expect(screen.getByText('bbbb2222')).toBeInTheDocument();
      expect(screen.getByText('cccc3333')).toBeInTheDocument();
      // Status pills
      expect(screen.getByText('Completed')).toBeInTheDocument();
      expect(screen.getByText('Failed')).toBeInTheDocument();
      expect(screen.getByText('Running')).toBeInTheDocument();
    });
  });

  it('renders delete buttons in job rows', async () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    await waitFor(() => {
      const deleteButtons = screen.getAllByTitle('Delete job');
      expect(deleteButtons).toHaveLength(3);
    });
  });
});
