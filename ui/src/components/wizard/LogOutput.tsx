/**
 * Props for the LogOutput component
 */
interface LogOutputProps {
  lines: string[];
}

/**
 * LogOutput component
 *
 * Displays log lines in a monospace font area with a muted background.
 * Used in the processing view to show redaction events.
 */
export function LogOutput({ lines }: LogOutputProps) {
  return (
    <div
      style={{
        marginTop: '24px',
        padding: '16px',
        backgroundColor: 'var(--bg-body)',
        borderRadius: '8px',
        fontFamily: 'monospace',
        fontSize: '13px',
        color: 'var(--text-secondary)',
        lineHeight: 1.8,
      }}
      role="log"
      aria-label="Processing log"
    >
      {lines.map((line, index) => (
        <div key={index}>{line}</div>
      ))}
    </div>
  );
}
