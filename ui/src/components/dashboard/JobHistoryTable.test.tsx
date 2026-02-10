import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { JobHistoryTable } from './JobHistoryTable';

describe('JobHistoryTable', () => {
  it('renders the table header columns', () => {
    render(<JobHistoryTable />);
    expect(screen.getByText('Job ID')).toBeInTheDocument();
    expect(screen.getByText('Source')).toBeInTheDocument();
    expect(screen.getByText('Date')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Action')).toBeInTheDocument();
  });

  it('renders job IDs in the rows', () => {
    render(<JobHistoryTable />);
    expect(screen.getByText('local-job-003')).toBeInTheDocument();
    expect(screen.getByText('local-job-002')).toBeInTheDocument();
  });

  it('renders source filenames', () => {
    render(<JobHistoryTable />);
    expect(screen.getByText('aws-prod-logs.jsonl')).toBeInTheDocument();
    expect(screen.getByText('user-db-dump.csv')).toBeInTheDocument();
  });

  it('renders dates', () => {
    render(<JobHistoryTable />);
    expect(screen.getByText('Today, 10:42 AM')).toBeInTheDocument();
    expect(screen.getByText('Yesterday, 4:15 PM')).toBeInTheDocument();
  });

  it('renders status pills with correct labels', () => {
    render(<JobHistoryTable />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('PII Detected')).toBeInTheDocument();
  });

  it('renders action buttons', () => {
    render(<JobHistoryTable />);
    expect(screen.getByText('View Report')).toBeInTheDocument();
    expect(screen.getByText('Review')).toBeInTheDocument();
  });

  it('renders with correct grid column layout', () => {
    const { container } = render(<JobHistoryTable />);
    const header = container.querySelector('[style*="text-transform"]') as HTMLElement;
    expect(header.style.gridTemplateColumns).toBe('2fr 2fr 2fr 1fr 1fr');
  });
});
