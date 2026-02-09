import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useScanProgress } from './useScanProgress';

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  readyState = 0; // CONNECTING

  constructor(_url: string) {
    MockWebSocket.instances.push(this);
  }

  close() {
    this.readyState = 3;
  }
}

describe('useScanProgress', () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    vi.stubGlobal('WebSocket', MockWebSocket);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns null progress when scanId is null', () => {
    const { result } = renderHook(() => useScanProgress(null));
    expect(result.current.progress).toBeNull();
    expect(result.current.isConnected).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('creates WebSocket connection when scanId is provided', () => {
    renderHook(() => useScanProgress('test-scan-id'));
    expect(MockWebSocket.instances).toHaveLength(1);
  });

  it('updates progress when WebSocket message is received', () => {
    const { result } = renderHook(() => useScanProgress('test-scan-id'));

    const ws = MockWebSocket.instances[0];
    act(() => {
      ws.onopen?.();
      ws.onmessage?.({
        data: JSON.stringify({
          scan_id: 'test-scan-id',
          status: 'running',
          records_processed: 5,
          total_records: null,
          percent_complete: null,
          elapsed_seconds: 2.5,
          error_type: null,
        }),
      });
    });

    expect(result.current.progress).not.toBeNull();
    expect(result.current.progress?.records_processed).toBe(5);
    expect(result.current.isConnected).toBe(true);
  });

  it('cleans up WebSocket on unmount', () => {
    const { unmount } = renderHook(() => useScanProgress('test-scan-id'));
    const ws = MockWebSocket.instances[0];
    unmount();
    expect(ws.readyState).toBe(3); // CLOSED
  });
});
