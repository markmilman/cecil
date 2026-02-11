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

  useEffect(() => {
    let cancelled = false;

    const startSanitization = async () => {
      try {
        setLogLines(['> Starting sanitization...']);
        const response = await apiClient.sanitize({
          source,
          mapping_id: mappingId,
          output_dir: outputDir,
        });

        if (cancelled) return;

        scanIdRef.current = response.scan_id;
        outputPathRef.current = response.output_path;
        setLogLines((prev) => [...prev, `> Scan ${response.scan_id} created.`]);

        // Start elapsed timer
        timerRef.current = setInterval(() => {
          setElapsedSeconds((prev) => prev + 1);
        }, 1000);

        // Connect WebSocket for live progress
        const port = import.meta.env.VITE_API_PORT || window.location.port || '8000';
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname || '127.0.0.1';
        const wsUrl = `${protocol}//${host}:${port}/api/v1/scans/${response.scan_id}/ws`;

        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onmessage = (event) => {
          if (cancelled || completedRef.current) return;

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
                if (!cancelled) {
                  onComplete({
                    outputPath: outputPathRef.current,
                    recordsProcessed: progress.records_processed,
                    recordsSanitized: progress.records_processed,
                  });
                }
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
          if (!cancelled && !completedRef.current) {
            setLogLines((prev) => [...prev, '> WebSocket connection error.']);
          }
        };

        ws.onclose = () => {
          // No-op — cleanup handled elsewhere
        };
      } catch (err) {
        if (!cancelled) {
          const message = err instanceof Error ? err.message : 'Failed to start sanitization';
          setError(message);
          setLogLines((prev) => [...prev, `> Error: ${message}`]);
        }
      }
    };

    startSanitization();

    return () => {
      cancelled = true;
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
              onClick={onStop}
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
            onClick={onStop}
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
