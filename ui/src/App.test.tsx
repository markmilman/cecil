import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { App } from './App';
import { FileFormat, ScanStatus } from '@/types';

// Mock the apiClient
vi.mock('@/lib/apiClient', () => ({
  apiClient: {
    uploadFiles: vi.fn(),
    sanitize: vi.fn(),
    listMappings: vi.fn(),
    listJobs: vi.fn(),
    loadMappingYaml: vi.fn(),
    getSampleRecord: vi.fn(),
  },
}));

import { apiClient } from '@/lib/apiClient';

// Mock WebSocket
class MockWebSocket {
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  close = vi.fn();
}

describe('App wizard reset', () => {
  beforeEach(() => {
    vi.mocked(apiClient.listJobs).mockResolvedValue([]);
    vi.mocked(apiClient.listMappings).mockResolvedValue([]);
    vi.mocked(apiClient.uploadFiles).mockResolvedValue({
      files: [
        {
          name: 'test.jsonl',
          path: '/tmp/uploads/test.jsonl',
          size: 1024,
          format: FileFormat.JSONL,
        },
      ],
      errors: [],
    });
    vi.mocked(apiClient.sanitize).mockResolvedValue({
      scan_id: 'scan-1',
      status: ScanStatus.RUNNING,
      source: '/tmp/uploads/test.jsonl',
      output_path: '~/.cecil/output/test.jsonl',
      records_processed: 0,
      records_sanitized: 0,
      records_failed: 0,
      created_at: '2026-01-01T00:00:00Z',
    });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (globalThis as any).WebSocket = MockWebSocket;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('resets wizard to step 1 when starting a new job after completing one', async () => {
    render(<App />);

    // Dashboard should render with "New Sanitization Job" button
    await waitFor(() => {
      expect(screen.getByText('New Sanitization Job')).toBeInTheDocument();
    });

    // Start the wizard — should show the upload step
    fireEvent.click(screen.getByText('New Sanitization Job'));
    await waitFor(() => {
      expect(screen.getByText('File Ingestion')).toBeInTheDocument();
    });

    // Upload a file to advance to step 2
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.jsonl', { type: 'application/json' });
    Object.defineProperty(fileInput, 'files', { value: [file], configurable: true });
    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText('Queued Files')).toBeInTheDocument();
    });

    // Now navigate back to dashboard using the sidebar
    const dashboardLink = screen.getByText('Dashboard');
    fireEvent.click(dashboardLink);
    await waitFor(() => {
      expect(screen.getByText('Audit Dashboard')).toBeInTheDocument();
    });

    // Start wizard again — must show step 1 (File Ingestion), not step 2
    fireEvent.click(screen.getByText('New Sanitization Job'));
    await waitFor(() => {
      expect(screen.getByText('File Ingestion')).toBeInTheDocument();
      expect(screen.getByText('Browse Files')).toBeInTheDocument();
    });
  });
});
