import { LoaderIcon } from 'lucide-react';
import type { ScanProgress } from '@/types';
import { ScanStatus } from '@/types';

interface IngestionProgressProps {
  progress: ScanProgress | null;
  isConnected: boolean;
}

/**
 * Format elapsed time in a human-readable format
 *
 * @param seconds - Elapsed time in seconds
 * @returns Formatted string (e.g., "1m 5s" or "42s")
 */
function formatElapsedTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  if (mins > 0) return `${mins}m ${secs}s`;
  return `${secs}s`;
}

/**
 * Get the status badge configuration for a given scan status
 *
 * @param status - The current scan status
 * @returns Badge label and Tailwind CSS classes
 */
function getStatusBadge(status: ScanStatus): { label: string; className: string } {
  switch (status) {
    case ScanStatus.PENDING:
      return { label: 'Pending', className: 'bg-slate-100 text-slate-600' };
    case ScanStatus.RUNNING:
      return { label: 'Running', className: 'bg-indigo-100 text-accent' };
    case ScanStatus.COMPLETED:
      return { label: 'Completed', className: 'bg-emerald-100 text-success' };
    case ScanStatus.FAILED:
      return { label: 'Failed', className: 'bg-red-100 text-danger' };
  }
}

/**
 * IngestionProgress component
 *
 * Displays real-time progress for an active scan operation. Shows a status badge,
 * progress bar (determinate or indeterminate), records processed count, and elapsed time.
 * Also displays connection status (Live for WebSocket, Polling for HTTP fallback).
 *
 * @param progress - Current scan progress data, or null if connecting
 * @param isConnected - Whether the WebSocket connection is active
 */
export function IngestionProgress({ progress, isConnected }: IngestionProgressProps) {
  if (!progress) {
    return (
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <div className="flex items-center gap-3 text-muted">
          <LoaderIcon className="h-5 w-5 animate-spin" />
          <span>Connecting...</span>
        </div>
      </div>
    );
  }

  const { label: statusLabel, className: statusClass } = getStatusBadge(progress.status);
  const isIndeterminate = progress.percent_complete === null;
  const isTerminal = progress.status === ScanStatus.COMPLETED || progress.status === ScanStatus.FAILED;

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-6">
      {/* Header: Status badge + connection indicator */}
      <div className="flex items-center justify-between mb-4">
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusClass}`}>
          {statusLabel}
        </span>
        {!isTerminal && (
          <span className={`text-xs ${isConnected ? 'text-success' : 'text-muted'}`}>
            {isConnected ? 'Live' : 'Polling'}
          </span>
        )}
      </div>

      {/* Progress bar */}
      <div
        role="progressbar"
        aria-label="Scan progress"
        aria-valuenow={progress.percent_complete ?? undefined}
        aria-valuemin={0}
        aria-valuemax={100}
        className="w-full h-2 bg-slate-100 rounded-full overflow-hidden mb-4"
      >
        {isIndeterminate && !isTerminal ? (
          <div className="h-full bg-accent rounded-full animate-pulse w-2/3" />
        ) : isTerminal && progress.status === ScanStatus.COMPLETED ? (
          <div className="h-full bg-success rounded-full w-full transition-all duration-300" />
        ) : isTerminal && progress.status === ScanStatus.FAILED ? (
          <div className="h-full bg-danger rounded-full w-full" />
        ) : (
          <div
            className="h-full bg-accent rounded-full transition-all duration-300"
            style={{ width: `${progress.percent_complete ?? 0}%` }}
          />
        )}
      </div>

      {/* Stats */}
      <div className="flex items-center justify-between" aria-live="polite">
        <div className="text-sm text-primary">
          <span className="font-medium">{progress.records_processed.toLocaleString()}</span>
          <span className="text-muted"> records processed</span>
        </div>
        <div className="text-sm text-muted">
          {formatElapsedTime(progress.elapsed_seconds)}
        </div>
      </div>
    </div>
  );
}
