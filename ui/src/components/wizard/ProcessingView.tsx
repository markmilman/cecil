import { useState, useEffect, useRef, useCallback } from 'react';
import { AlertCircleIcon } from 'lucide-react';
import { WizardHeader } from './WizardHeader';
import { ProgressCard } from './ProgressCard';
import { LogOutput } from './LogOutput';
import { apiClient } from '@/lib/apiClient';
import type { ScanProgress } from '@/types';

interface SanitizeResult {
  outputPath: string;
  recordsProcessed: number;
  recordsSanitized: number;
}

interface ProcessingViewProps {
  source: string;
  mappingId: string;
  outputDir: string;
  onComplete: (result: SanitizeResult) => void;
  onStop: () => void;
}

/**
 * ProcessingView component (Wizard Step 4)
 *
 * Initiates a real sanitization run via the API, then monitors
 * progress over a WebSocket connection. Displays a progress card
 * with animated progress bar, record count, elapsed timer, and
 * a log output area. Includes a "Stop Process" danger button.
 * When the scan completes, auto-advances after a brief delay.
 */
export function ProcessingView({
  source,
  mappingId,
  outputDir,
  onComplete,
  onStop,
}: ProcessingViewProps) {
  const [percentComplete, setPercentComplete] = useState(0);
  const [recordsProcessed, setRecordsProcessed] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [logLines, setLogLines] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const completedRef = useRef(false);
  const scanIdRef = useRef<string | null>(null);
  const outputPathRef = useRef<string>('');
  const startedRef = useRef(false);

  const cleanup = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const handleStop = useCallback(async () => {
    if (scanIdRef.current) {
      try {
        await apiClient.cancelScan(scanIdRef.current);
        setLogLines((prev) => [...prev, '> Cancellation requested...']);
      } catch (err) {
        // Log error but still allow navigation back
        console.error('Failed to cancel scan:', err);
      }
    }
    cleanup();
    onStop();
  }, [cleanup, onStop]);

  useEffect(() => {
    // Guard against React StrictMode double-firing the effect,
    // which would create two sanitization jobs on the backend.
    // The ref persists across the StrictMode unmount/remount cycle,
    // so the second invocation is a no-op.  We intentionally avoid
    // a local `cancelled` flag because StrictMode's cleanup would
    // set it to true before the async API response arrives, causing
    // the single legitimate call's result to be discarded.
    // Instead we rely on `completedRef` (double-completion guard)
    // and `cleanup()` (resource teardown on real unmount).
    if (startedRef.current) return;
    startedRef.current = true;

    const startSanitization = async () => {
      try {
        setLogLines(['> Starting sanitization...']);
        const response = await apiClient.sanitize({
          source,
          mapping_id: mappingId,
          output_dir: outputDir,
        });

        scanIdRef.current = response.scan_id;
        outputPathRef.current = response.output_path;
        setLogLines((prev) => [...prev, `> Scan ${response.scan_id} created.`]);

        // Start elapsed timer
        timerRef.current = setInterval(() => {
          setElapsedSeconds((prev) => prev + 1);
        }, 1000);

        // Connect WebSocket for live progress.
        // Must match the host used by apiClient (127.0.0.1 when VITE_API_PORT
        // is set) to avoid IPv4/IPv6 mismatches on macOS where "localhost"
        // can resolve to ::1 while FastAPI binds to 127.0.0.1 only.
        const envPort = import.meta.env.VITE_API_PORT;
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        let wsUrl: string;
        if (envPort) {
          wsUrl = `ws://127.0.0.1:${envPort}/api/v1/scans/${response.scan_id}/ws`;
        } else {
          const host = window.location.hostname || '127.0.0.1';
          const port = window.location.port || '8000';
          wsUrl = `${protocol}//${host}:${port}/api/v1/scans/${response.scan_id}/ws`;
        }

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onmessage = (event) => {
          if (completedRef.current) return;

          try {
            const progress: ScanProgress = JSON.parse(event.data);
            setRecordsProcessed(progress.records_processed);
            setPercentComplete(progress.percent_complete ?? 0);
            setElapsedSeconds(progress.elapsed_seconds);
            setLogLines((prev) => [
              ...prev,
              `> Processing... ${progress.records_processed} records`,
            ]);

            if (progress.status === 'completed' && !completedRef.current) {
              completedRef.current = true;
              setPercentComplete(100);
              setLogLines((prev) => [...prev, '> Sanitization complete.']);
              cleanup();
              setTimeout(() => {
                onComplete({
                  outputPath: outputPathRef.current,
                  recordsProcessed: progress.records_processed,
                  recordsSanitized: progress.records_processed,
                });
              }, 500);
            } else if (progress.status === 'failed') {
              cleanup();
              setError(progress.error_type ?? 'Sanitization failed');
              setLogLines((prev) => [
                ...prev,
                `> Error: ${progress.error_type ?? 'Unknown error'}`,
              ]);
            }
          } catch {
            // Ignore malformed messages
          }
        };

        ws.onerror = () => {
          if (!completedRef.current) {
            setLogLines((prev) => [...prev, '> WebSocket connection error.']);
          }
        };

        ws.onclose = () => {
          // No-op — cleanup handled elsewhere
        };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to start sanitization';
        setError(message);
        setLogLines((prev) => [...prev, `> Error: ${message}`]);
      }
    };

    startSanitization();

    return () => {
      cleanup();
    };
  }, [source, mappingId, outputDir, onComplete, cleanup]);

  if (error) {
    return (
      <div>
        <WizardHeader
          title="Sanitization Error"
          subtitle="An error occurred during processing."
          action={
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleStop}
            >
              Back
            </button>
          }
        />
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <div
            className="flex items-center gap-2"
            style={{
              padding: '12px 16px',
              backgroundColor: 'var(--danger-bg)',
              border: '1px solid var(--danger-border)',
              borderRadius: '8px',
              marginBottom: '16px',
              color: 'var(--danger-color)',
              fontSize: '14px',
            }}
          >
            <AlertCircleIcon className="h-4 w-4" />
            {error}
          </div>
          <LogOutput lines={logLines} />
        </div>
      </div>
    );
  }

  return (
    <div>
      <WizardHeader
        title="Sanitizing Files..."
        subtitle="Please wait while we scrub PII locally."
        action={
          <button
            type="button"
            className="btn btn-danger"
            onClick={handleStop}
          >
            Stop Process
          </button>
        }
      />

      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <ProgressCard
          percentComplete={percentComplete}
          recordCount={recordsProcessed}
          elapsedSeconds={elapsedSeconds}
        />

        <LogOutput lines={logLines} />
      </div>
    </div>
  );
}
