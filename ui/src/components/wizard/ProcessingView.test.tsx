import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { ProcessingView } from './ProcessingView';
import { ScanStatus } from '@/types';

// Mock the apiClient
vi.mock('@/lib/apiClient', () => ({
  apiClient: {
    sanitize: vi.fn(),
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

const defaultProps = {
  source: '/tmp/test.jsonl',
  mappingId: 'mapping-123',
  outputDir: '~/.cecil/output/',
  onComplete: vi.fn(),
  onStop: vi.fn(),
};

describe('ProcessingView', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.mocked(apiClient.sanitize).mockResolvedValue({
      scan_id: 'scan-1',
      status: ScanStatus.RUNNING,
      source: '/tmp/test.jsonl',
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
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('renders the heading after API call', async () => {
    vi.useRealTimers();
    render(<ProcessingView {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText('Sanitizing Files...')).toBeInTheDocument();
    });
  });

  it('renders the subtitle', async () => {
    vi.useRealTimers();
    render(<ProcessingView {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText('Please wait while we scrub PII locally.')).toBeInTheDocument();
    });
  });

  it('renders the Stop Process button', async () => {
    vi.useRealTimers();
    render(<ProcessingView {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText('Stop Process')).toBeInTheDocument();
    });
  });

  it('renders a progress bar with role progressbar', async () => {
    vi.useRealTimers();
    render(<ProcessingView {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  it('has an accessible log area', async () => {
    vi.useRealTimers();
    render(<ProcessingView {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByRole('log')).toBeInTheDocument();
    });
  });

  it('calls onStop when Stop Process is clicked', async () => {
    vi.useRealTimers();
    const onStop = vi.fn();
    render(<ProcessingView {...defaultProps} onStop={onStop} />);
    await waitFor(() => {
      expect(screen.getByText('Stop Process')).toBeInTheDocument();
    });
    screen.getByText('Stop Process').click();
    expect(onStop).toHaveBeenCalledOnce();
  });

  it('shows error state when API call fails', async () => {
    vi.useRealTimers();
    vi.mocked(apiClient.sanitize).mockRejectedValue(new Error('Server error'));
    render(<ProcessingView {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText('Server error')).toBeInTheDocument();
    });
  });

  it('shows initial log line', async () => {
    vi.useRealTimers();
    render(<ProcessingView {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText('> Starting sanitization...')).toBeInTheDocument();
    });
  });
});
