import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IngestionProgress } from './IngestionProgress';
import { ScanStatus } from '@/types';
import type { ScanProgress } from '@/types';

const makeProgress = (overrides: Partial<ScanProgress> = {}): ScanProgress => ({
  scan_id: 'test-scan',
  status: ScanStatus.RUNNING,
  records_processed: 42,
  total_records: null,
  percent_complete: null,
  elapsed_seconds: 10,
  error_type: null,
  ...overrides,
});

describe('IngestionProgress', () => {
  it('shows connecting state when progress is null', () => {
    render(<IngestionProgress progress={null} isConnected={false} />);
    expect(screen.getByText('Connecting...')).toBeInTheDocument();
  });

  it('renders the progress bar with correct ARIA attributes', () => {
    render(<IngestionProgress progress={makeProgress()} isConnected={true} />);
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-label', 'Scan progress');
  });

  it('displays records processed count', () => {
    render(<IngestionProgress progress={makeProgress({ records_processed: 42 })} isConnected={true} />);
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('records processed')).toBeInTheDocument();
  });

  it('displays elapsed time', () => {
    render(<IngestionProgress progress={makeProgress({ elapsed_seconds: 65 })} isConnected={true} />);
    expect(screen.getByText('1m 5s')).toBeInTheDocument();
  });

  it('shows Running status badge when running', () => {
    render(<IngestionProgress progress={makeProgress()} isConnected={true} />);
    expect(screen.getByText('Running')).toBeInTheDocument();
  });

  it('shows Completed status badge when completed', () => {
    render(<IngestionProgress progress={makeProgress({ status: ScanStatus.COMPLETED })} isConnected={false} />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('shows connection indicator as Live when connected', () => {
    render(<IngestionProgress progress={makeProgress()} isConnected={true} />);
    expect(screen.getByText('Live')).toBeInTheDocument();
  });
});
