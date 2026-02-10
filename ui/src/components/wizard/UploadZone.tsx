import { UploadIcon } from 'lucide-react';
import { WizardHeader } from './WizardHeader';
import { TrustBadge } from './TrustBadge';

/**
 * Props for the UploadZone component
 */
interface UploadZoneProps {
  onBrowseFiles: () => void;
}

/**
 * UploadZone component (Wizard Step 1)
 *
 * Displays a drag-and-drop upload zone with a dashed border,
 * heading, subtitle, and "Browse Files" button. The upload zone
 * border changes to primary color on hover.
 */
export function UploadZone({ onBrowseFiles }: UploadZoneProps) {
  return (
    <div>
      <WizardHeader
        title="File Ingestion"
        subtitle="Select local files to sanitize. Data stays on your device."
        action={<TrustBadge />}
      />

      <div style={{ maxWidth: '800px', margin: '40px auto' }}>
        <div
          className="cursor-pointer text-center transition-colors duration-200"
          style={{
            border: '2px dashed var(--border-color)',
            borderRadius: '12px',
            padding: '60px',
            backgroundColor: 'var(--bg-body)',
          }}
          onClick={onBrowseFiles}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              onBrowseFiles();
            }
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--primary-color)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--border-color)';
          }}
          role="button"
          tabIndex={0}
          aria-label="Browse files for upload"
        >
          <div style={{ marginBottom: '16px' }}>
            <UploadIcon
              className="mx-auto h-12 w-12"
              style={{ color: 'var(--text-secondary)' }}
            />
          </div>
          <h3
            style={{
              margin: '0 0 8px 0',
              color: 'var(--text-primary)',
            }}
          >
            Drag and drop log files
          </h3>
          <p
            style={{
              margin: 0,
              color: 'var(--text-secondary)',
            }}
          >
            Supported: JSONL, CSV, Parquet
          </p>
          <button
            type="button"
            className="btn btn-primary"
            style={{ marginTop: '24px' }}
            onClick={(e) => {
              e.stopPropagation();
              onBrowseFiles();
            }}
          >
            Browse Files
          </button>
        </div>
      </div>
    </div>
  );
}
