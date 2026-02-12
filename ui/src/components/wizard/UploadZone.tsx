import { useRef } from 'react';
import { UploadIcon } from 'lucide-react';
import { WizardHeader } from './WizardHeader';
import { TrustBadge } from './TrustBadge';

/**
 * Props for the UploadZone component
 */
interface UploadZoneProps {
  onBrowseFiles: (files: FileList) => void;
  isUploading?: boolean;
  uploadError?: string | null;
}

/**
 * UploadZone component (Wizard Step 1)
 *
 * Displays a drag-and-drop upload zone with a dashed border,
 * heading, subtitle, and "Browse Files" button. Opens the browser's
 * native file picker when clicked.
 */
export function UploadZone({ onBrowseFiles, isUploading = false, uploadError = null }: UploadZoneProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onBrowseFiles(files);
    }
    // Reset input so the same file can be re-selected
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div>
      <WizardHeader
        title="File Ingestion"
        subtitle="Select local files to sanitize. Data stays on your device."
        action={<TrustBadge />}
      />

      <div style={{ maxWidth: '800px', margin: '40px auto' }}>
        <div
          className={`cursor-pointer text-center transition-colors duration-200 ${isUploading ? 'opacity-50 pointer-events-none' : ''}`}
          style={{
            border: '2px dashed var(--border-color)',
            borderRadius: '12px',
            padding: '60px',
            backgroundColor: 'var(--bg-body)',
          }}
          onClick={handleClick}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              handleClick();
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
            {isUploading ? 'Uploading...' : 'Drag and drop log files'}
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
            disabled={isUploading}
            onClick={(e) => {
              e.stopPropagation();
              handleClick();
            }}
          >
            {isUploading ? 'Uploading...' : 'Browse Files'}
          </button>
        </div>

        {uploadError && (
          <div
            style={{
              marginTop: '16px',
              padding: '12px',
              backgroundColor: 'var(--danger-bg, #fef2f2)',
              border: '1px solid var(--danger-border, #fecaca)',
              borderRadius: '8px',
              color: 'var(--danger-color)',
              fontSize: '14px',
              textAlign: 'center',
            }}
          >
            {uploadError}
          </div>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".jsonl,.csv,.parquet"
        onChange={handleFileChange}
        className="hidden"
        style={{ display: 'none' }}
      />
    </div>
  );
}
