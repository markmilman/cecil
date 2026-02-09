import { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient } from '@/lib/apiClient';
import type { ScanProgress, ScanStatus } from '@/types';

interface UseScanProgressResult {
  progress: ScanProgress | null;
  isConnected: boolean;
  error: string | null;
}

/**
 * Custom hook for real-time scan progress tracking via WebSocket
 *
 * Connects to the WebSocket endpoint for a given scan ID and streams
 * ScanProgress updates. Falls back to HTTP polling if the WebSocket
 * connection fails or times out.
 *
 * @param scanId - The scan ID to track, or null to disconnect
 * @returns Progress data, connection status, and error state
 */
export function useScanProgress(scanId: string | null): UseScanProgressResult {
  const [progress, setProgress] = useState<ScanProgress | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Derive WebSocket URL from apiClient base URL
  const getWsUrl = useCallback((id: string): string => {
    const baseURL = apiClient.getClient().defaults.baseURL || 'http://127.0.0.1:8000';
    const wsBase = baseURL.replace(/^http/, 'ws');
    return `${wsBase}/api/v1/scans/${id}/ws`;
  }, []);

  // Polling fallback using GET /api/v1/scans/{scanId}
  const startPolling = useCallback((id: string) => {
    if (pollingRef.current) return;
    pollingRef.current = setInterval(async () => {
      try {
        const response = await apiClient.getScan(id);
        const fallbackProgress: ScanProgress = {
          scan_id: response.scan_id,
          status: response.status as ScanStatus,
          records_processed: response.records_processed,
          total_records: null,
          percent_complete: null,
          elapsed_seconds: 0,
          error_type: response.errors.length > 0 ? response.errors[0] : null,
        };
        setProgress(fallbackProgress);
        // Stop polling on terminal states
        if (response.status === 'completed' || response.status === 'failed') {
          if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
        }
      } catch {
        // Silently retry on next interval
      }
    }, 1000);
  }, []);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!scanId) {
      setProgress(null);
      setIsConnected(false);
      setError(null);
      return;
    }

    setError(null);
    const wsUrl = getWsUrl(scanId);

    // Connection timeout — fall back to polling if WS doesn't connect in 3s
    const connectionTimeout = setTimeout(() => {
      if (wsRef.current && wsRef.current.readyState !== WebSocket.OPEN) {
        wsRef.current.close();
        startPolling(scanId);
      }
    }, 3000);

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      clearTimeout(connectionTimeout);
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string) as ScanProgress;
        setProgress(data);
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onerror = () => {
      clearTimeout(connectionTimeout);
      setIsConnected(false);
      setError('WebSocket connection failed');
      startPolling(scanId);
    };

    ws.onclose = () => {
      clearTimeout(connectionTimeout);
      setIsConnected(false);
    };

    return () => {
      clearTimeout(connectionTimeout);
      stopPolling();
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [scanId, getWsUrl, startPolling, stopPolling]);

  return { progress, isConnected, error };
}
