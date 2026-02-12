import { EyeIcon } from 'lucide-react';

interface LocalOutputCardProps {
  outputPath: string;
  onOpenFolder?: () => void;
  onViewResults?: () => void;
}

/**
 * Local Output card for the wizard completion view.
 *
 * Shows the output directory path in a code block and action buttons
 * for opening the folder and viewing sanitized results. Used in Step 5
 * to let users access and review their sanitized files.
 */
export function LocalOutputCard({ outputPath, onOpenFolder, onViewResults }: LocalOutputCardProps) {
  return (
    <div
      style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: '12px',
        padding: '24px',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <h3
        style={{
          margin: '0 0 8px',
          fontSize: '16px',
          color: 'var(--text-primary)',
        }}
      >
        Local Output
      </h3>
      <p
        style={{
          fontSize: '14px',
          color: 'var(--text-secondary)',
          margin: '0 0 12px',
        }}
      >
        Files saved to:
      </p>
      <div
        style={{
          backgroundColor: 'var(--bg-body)',
          padding: '8px 12px',
          borderRadius: '4px',
          fontFamily: 'monospace',
          fontSize: '12px',
          marginBottom: '16px',
          color: 'var(--text-primary)',
        }}
      >
        {outputPath}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <button
          type="button"
          className="btn btn-primary"
          style={{ width: '100%', justifyContent: 'center', gap: '8px' }}
          onClick={onViewResults}
        >
          <EyeIcon className="h-4 w-4" />
          View Results
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          style={{ width: '100%', justifyContent: 'center' }}
          onClick={onOpenFolder}
        >
          Open Folder
        </button>
      </div>
    </div>
  );
}
