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
 * @returns Badge label and Tailwind CSS classes (WCAG 4.5:1+ contrast)
 */
function getStatusBadge(status: ScanStatus): { label: string; className: string } {
  switch (status) {
    case ScanStatus.PENDING:
      return { label: 'Pending', className: 'bg-slate-100 text-slate-700' };
    case ScanStatus.RUNNING:
      return { label: 'Running', className: 'bg-indigo-100 text-indigo-700' };
    case ScanStatus.COMPLETED:
      return { label: 'Completed', className: 'bg-emerald-100 text-emerald-700' };
    case ScanStatus.FAILED:
      return { label: 'Failed', className: 'bg-red-100 text-red-700' };
  }
}

/**
 * Shimmer skeleton loading state
 */
function ShimmerSkeleton() {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-8 shadow-sm">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-6 w-24 rounded-full bg-slate-200 animate-shimmer" />
          <div className="h-4 w-12 rounded bg-slate-200 animate-shimmer" />
        </div>
        <div className="h-3 w-full rounded-full bg-slate-200 animate-shimmer" />
        <div className="flex items-center justify-between">
          <div className="h-4 w-40 rounded bg-slate-200 animate-shimmer" />
          <div className="h-4 w-16 rounded bg-slate-200 animate-shimmer" />
        </div>
      </div>
    </div>
  );
}

/**
 * IngestionProgress component (v2)
 *
 * Displays real-time progress for an active scan operation. Shows a status badge,
 * progress bar (determinate or indeterminate), records processed count, and elapsed time.
 * V2: shimmer skeleton loading, h-3 progress bar with shadow, smooth easing,
 * WCAG-compliant badge contrast.
 *
 * @param progress - Current scan progress data, or null if connecting
 * @param isConnected - Whether the WebSocket connection is active
 */
export function IngestionProgress({ progress, isConnected }: IngestionProgressProps) {
  if (!progress) {
    return <ShimmerSkeleton />;
  }

  const { label: statusLabel, className: statusClass } = getStatusBadge(progress.status);
  const isIndeterminate = progress.percent_complete === null;
  const isTerminal = progress.status === ScanStatus.COMPLETED || progress.status === ScanStatus.FAILED;

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-8 shadow-sm hover:shadow-md transition-shadow duration-200">
      {/* Header: Status badge + connection indicator */}
      <div className="flex items-center justify-between mb-4">
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusClass}`}>
          {statusLabel}
        </span>
        {!isTerminal && (
          <span className={`text-xs font-medium ${isConnected ? 'text-emerald-600' : 'text-slate-500'}`}>
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
        className="w-full h-3 bg-slate-100 rounded-full overflow-hidden mb-4 shadow-sm"
      >
        {isIndeterminate && !isTerminal ? (
          <div className="h-full bg-accent rounded-full w-1/3 animate-progress-indeterminate" />
        ) : isTerminal && progress.status === ScanStatus.COMPLETED ? (
          <div className="h-full bg-emerald-500 rounded-full w-full transition-all duration-500 ease-out" />
        ) : isTerminal && progress.status === ScanStatus.FAILED ? (
          <div className="h-full bg-red-500 rounded-full w-full" />
        ) : (
          <div
            className="h-full bg-accent rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress.percent_complete ?? 0}%` }}
          />
        )}
      </div>

      {/* Stats */}
      <div className="flex items-center justify-between" aria-live="polite">
        <div className="text-sm text-primary">
          <span className="font-semibold">{progress.records_processed.toLocaleString()}</span>
          <span className="text-slate-600"> records processed</span>
        </div>
        <div className="text-sm text-slate-600">
          {formatElapsedTime(progress.elapsed_seconds)}
        </div>
      </div>
    </div>
  );
}
