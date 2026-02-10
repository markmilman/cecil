import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { WizardContainer } from './WizardContainer';

describe('WizardContainer', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('starts at step 1 with UploadZone', () => {
    render(<WizardContainer onBackToDashboard={vi.fn()} />);
    expect(screen.getByText('File Ingestion')).toBeInTheDocument();
    expect(screen.getByText('Browse Files')).toBeInTheDocument();
  });

  it('advances to step 2 when Browse Files is clicked', () => {
    render(<WizardContainer onBackToDashboard={vi.fn()} />);
    fireEvent.click(screen.getByText('Browse Files'));
    expect(screen.getByText('Queued Files')).toBeInTheDocument();
  });

  it('shows mock files in step 2 after browsing', () => {
    render(<WizardContainer onBackToDashboard={vi.fn()} />);
    fireEvent.click(screen.getByText('Browse Files'));
    expect(screen.getByText('app-logs-prod.jsonl')).toBeInTheDocument();
    expect(screen.getByText('api-requests-2024.csv')).toBeInTheDocument();
    expect(screen.getByText('user-sessions.parquet')).toBeInTheDocument();
  });

  it('goes back to step 1 when Cancel is clicked in step 2', () => {
    render(<WizardContainer onBackToDashboard={vi.fn()} />);
    fireEvent.click(screen.getByText('Browse Files'));
    fireEvent.click(screen.getByText('Cancel'));
    expect(screen.getByText('File Ingestion')).toBeInTheDocument();
  });

  it('removes a file from the queue', () => {
    render(<WizardContainer onBackToDashboard={vi.fn()} />);
    fireEvent.click(screen.getByText('Browse Files'));
    fireEvent.click(screen.getByRole('button', { name: 'Remove app-logs-prod.jsonl' }));
    expect(screen.queryByText('app-logs-prod.jsonl')).not.toBeInTheDocument();
    expect(screen.getByText('2 Files selected for sanitization.')).toBeInTheDocument();
  });

  it('advances to step 3 when Sanitize button is clicked', () => {
    render(<WizardContainer onBackToDashboard={vi.fn()} />);
    fireEvent.click(screen.getByText('Browse Files'));
    fireEvent.click(screen.getByText('Sanitize 3 Files'));
    expect(screen.getByText('Sanitizing Files...')).toBeInTheDocument();
  });

  it('goes back to step 2 when Stop Process is clicked in step 3', () => {
    render(<WizardContainer onBackToDashboard={vi.fn()} />);
    fireEvent.click(screen.getByText('Browse Files'));
    fireEvent.click(screen.getByText('Sanitize 3 Files'));
    fireEvent.click(screen.getByText('Stop Process'));
    expect(screen.getByText('Queued Files')).toBeInTheDocument();
  });
});
