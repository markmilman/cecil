/**
 * Props for the ProgressCard component
 */
interface ProgressCardProps {
  percentComplete: number;
  recordCount: number;
  elapsedSeconds: number;
}

/**
 * Format elapsed seconds as MM:SS
 */
function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

/**
 * ProgressCard component
 *
 * Displays a card with "Running" status pill, elapsed timer,
 * animated progress bar, record count, and "Live" indicator.
 * The progress bar width is driven by the percentComplete prop.
 */
export function ProgressCard({
  percentComplete,
  recordCount,
  elapsedSeconds,
}: ProgressCardProps) {
  return (
    <div
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '32px',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      {/* Header: Status Pill + Timer */}
      <div
        className="flex items-center justify-between"
        style={{ marginBottom: '8px' }}
      >
        <span
          className="inline-block rounded-full px-3 py-1 text-xs font-semibold"
          style={{
            backgroundColor: 'var(--primary-light)',
            color: 'var(--primary-color)',
          }}
        >
          Running
        </span>
        <span
          style={{
            fontFamily: 'monospace',
            color: 'var(--text-secondary)',
          }}
        >
          {formatTime(elapsedSeconds)}
        </span>
      </div>

      {/* Progress Bar */}
      <div
        style={{
          height: '8px',
          backgroundColor: 'var(--bg-body)',
          borderRadius: '4px',
          margin: '24px 0 12px',
          overflow: 'hidden',
        }}
        role="progressbar"
        aria-valuenow={percentComplete}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Sanitization progress"
      >
        <div
          style={{
            height: '100%',
            backgroundColor: 'var(--primary-color)',
            width: `${percentComplete}%`,
            transition: 'width 0.3s ease',
          }}
        />
      </div>

      {/* Footer: Record Count + Live Indicator */}
      <div
        className="flex items-center justify-between"
        style={{ fontSize: '14px', marginTop: '8px' }}
      >
        <span style={{ color: 'var(--text-primary)' }}>
          {recordCount.toLocaleString()} records sanitized
        </span>
        <span style={{ color: 'var(--success-color)' }}>Live</span>
      </div>
    </div>
  );
}
