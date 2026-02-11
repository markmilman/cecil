import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WizardContainer } from './WizardContainer';
import { FileFormat } from '@/types';

// Mock the apiClient
vi.mock('@/lib/apiClient', () => ({
  apiClient: {
    uploadFiles: vi.fn(),
  },
}));

// Import after mock setup
import { apiClient } from '@/lib/apiClient';

const MOCK_UPLOAD_RESPONSE = {
  files: [
    { name: 'app-logs-prod.jsonl', path: '/tmp/uploads/app-logs-prod.jsonl', size: 2516582, format: FileFormat.JSONL },
    { name: 'api-requests-2024.csv', path: '/tmp/uploads/api-requests-2024.csv', size: 911360, format: FileFormat.CSV },
  ],
  errors: [],
};

describe('WizardContainer', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.mocked(apiClient.uploadFiles).mockResolvedValue(MOCK_UPLOAD_RESPONSE);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('starts at step 1 with UploadZone', () => {
    render(<WizardContainer onBackToDashboard={vi.fn()} />);
    expect(screen.getByText('File Ingestion')).toBeInTheDocument();
    expect(screen.getByText('Browse Files')).toBeInTheDocument();
  });

  it('advances to step 2 after file upload', async () => {
    vi.useRealTimers();
    render(<WizardContainer onBackToDashboard={vi.fn()} />);

    // Simulate selecting files via the hidden input
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test content'], 'test.jsonl', { type: 'application/json' });
    Object.defineProperty(fileInput, 'files', { value: [file], configurable: true });
    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText('Queued Files')).toBeInTheDocument();
    });
  });

  it('shows uploaded files in step 2', async () => {
    vi.useRealTimers();
    render(<WizardContainer onBackToDashboard={vi.fn()} />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.jsonl', { type: 'application/json' });
    Object.defineProperty(fileInput, 'files', { value: [file], configurable: true });
    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText('app-logs-prod.jsonl')).toBeInTheDocument();
      expect(screen.getByText('api-requests-2024.csv')).toBeInTheDocument();
    });
  });

  it('goes back to step 1 when Cancel is clicked in step 2', async () => {
    vi.useRealTimers();
    render(<WizardContainer onBackToDashboard={vi.fn()} />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.jsonl', { type: 'application/json' });
    Object.defineProperty(fileInput, 'files', { value: [file], configurable: true });
    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Cancel'));
    expect(screen.getByText('File Ingestion')).toBeInTheDocument();
  });

  it('advances to step 3 when Sanitize button is clicked', async () => {
    vi.useRealTimers();
    render(<WizardContainer onBackToDashboard={vi.fn()} />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.jsonl', { type: 'application/json' });
    Object.defineProperty(fileInput, 'files', { value: [file], configurable: true });
    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText('Sanitize 2 Files')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Sanitize 2 Files'));
    expect(screen.getByText('Sanitizing Files...')).toBeInTheDocument();
  });

  it('goes back to step 2 when Stop Process is clicked in step 3', async () => {
    vi.useRealTimers();
    render(<WizardContainer onBackToDashboard={vi.fn()} />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.jsonl', { type: 'application/json' });
    Object.defineProperty(fileInput, 'files', { value: [file], configurable: true });
    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText('Sanitize 2 Files')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Sanitize 2 Files'));
    fireEvent.click(screen.getByText('Stop Process'));
    expect(screen.getByText('Queued Files')).toBeInTheDocument();
  });
});
