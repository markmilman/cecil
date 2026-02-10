import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IngestPage } from './IngestPage';
import { getErrorMessage } from '@/lib/errorMessages';

// Mock the FileBrowserModal to avoid API calls
vi.mock('@/components/ingestion/FileBrowserModal', () => ({
  FileBrowserModal: ({ isOpen }: { isOpen: boolean }) => {
    if (!isOpen) return null;
    return <div data-testid="file-browser-modal" />;
  },
}));

describe('IngestPage', () => {
  it('renders the page heading', () => {
    render(<IngestPage />);
    expect(screen.getByText('File Ingestion')).toBeInTheDocument();
  });

  it('renders the file picker with Browse Files button', () => {
    render(<IngestPage />);
    expect(screen.getByText('Browse Files')).toBeInTheDocument();
  });

  it('renders the file picker empty state heading', () => {
    render(<IngestPage />);
    expect(screen.getByText('Select a Data File to Get Started')).toBeInTheDocument();
  });

  it('renders the format selector', () => {
    render(<IngestPage />);
    expect(screen.getByText('File Format')).toBeInTheDocument();
  });

  it('renders the submit button', () => {
    render(<IngestPage />);
    expect(screen.getByText('Start Scan')).toBeInTheDocument();
  });

  it('disables submit button when no file is selected', () => {
    render(<IngestPage />);
    expect(screen.getByText('Start Scan')).toBeDisabled();
  });
});

describe('getErrorMessage', () => {
  it('returns correct message for ProviderConnectionError', () => {
    expect(getErrorMessage('ProviderConnectionError')).toContain('could not be found');
  });

  it('returns correct message for file_not_found', () => {
    expect(getErrorMessage('file_not_found')).toContain('could not be found');
  });

  it('returns correct message for ProviderReadError', () => {
    expect(getErrorMessage('ProviderReadError')).toContain('could not be parsed');
  });

  it('returns correct message for parse_error', () => {
    expect(getErrorMessage('parse_error')).toContain('could not be parsed');
  });

  it('returns correct message for memory_exceeded', () => {
    expect(getErrorMessage('memory_exceeded')).toContain('exceeds the maximum processing size');
  });

  it('returns correct message for ProviderDependencyError', () => {
    expect(getErrorMessage('ProviderDependencyError')).toContain('required dependency is not installed');
  });

  it('returns default message for unknown error', () => {
    expect(getErrorMessage('UnknownError')).toContain('unexpected error');
  });

  it('returns default message for null error type', () => {
    expect(getErrorMessage(null)).toContain('unexpected error');
  });
});
