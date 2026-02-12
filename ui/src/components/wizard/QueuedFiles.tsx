import { FileTextIcon, XIcon, ArrowLeftIcon } from 'lucide-react';
import { WizardHeader } from './WizardHeader';
import { TrustBadge } from './TrustBadge';
import type { UploadedFileInfo } from '@/types';

/**
 * Props for the QueuedFiles component
 */
interface QueuedFilesProps {
  files: UploadedFileInfo[];
  onRemoveFile: (index: number) => void;
  onCancel: () => void;
  onSanitize: () => void;
  onBack: () => void;
}

/**
 * Format file size in human-readable format
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const size = bytes / Math.pow(1024, i);
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

/**
 * QueuedFiles component (Wizard Step 2)
 *
 * Shows a list of uploaded files with file icons, name/size/format,
 * and remove buttons. Includes Back, Cancel, and "Sanitize N Files"
 * action buttons in a footer.
 */
export function QueuedFiles({
  files,
  onRemoveFile,
  onCancel,
  onSanitize,
  onBack,
}: QueuedFilesProps) {
  return (
    <div>
      <WizardHeader
        title="Queued Files"
        subtitle={`${files.length} File${files.length !== 1 ? 's' : ''} selected for sanitization.`}
        action={<TrustBadge />}
      />

      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        {/* File List */}
        <div
          className="flex flex-col"
          style={{ gap: '12px', margin: '24px 0' }}
        >
          {files.map((file, index) => (
            <div
              key={`${file.name}-${file.path}`}
              className="flex items-center justify-between"
              style={{
                padding: '16px',
                backgroundColor: 'var(--bg-body)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
              }}
            >
              <div className="flex items-center" style={{ gap: '12px' }}>
                <FileTextIcon
                  className="h-5 w-5"
                  style={{ color: 'var(--text-secondary)' }}
                />
                <div>
                  <div
                    style={{
                      fontWeight: 600,
                      color: 'var(--text-primary)',
                    }}
                  >
                    {file.name}
                  </div>
                  <div
                    className="flex items-center"
                    style={{
                      fontSize: '12px',
                      color: 'var(--text-secondary)',
                      gap: '8px',
                    }}
                  >
                    {file.format && (
                      <span
                        style={{
                          padding: '1px 6px',
                          backgroundColor: 'var(--primary-bg, #eef2ff)',
                          color: 'var(--primary-color)',
                          borderRadius: '4px',
                          fontWeight: 500,
                          textTransform: 'uppercase',
                          fontSize: '11px',
                        }}
                      >
                        {file.format}
                      </span>
                    )}
                    <span>{formatFileSize(file.size)}</span>
                  </div>
                </div>
              </div>
              <button
                type="button"
                onClick={() => onRemoveFile(index)}
                className="cursor-pointer border-none bg-transparent transition-colors duration-200"
                style={{ color: 'var(--text-secondary)' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.color = 'var(--danger-color)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.color = 'var(--text-secondary)';
                }}
                aria-label={`Remove ${file.name}`}
              >
                <XIcon className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>

        {/* Footer Actions */}
        <div
          className="flex items-center justify-between"
          style={{
            borderTop: '1px solid var(--border-color)',
            paddingTop: '24px',
          }}
        >
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onBack}
          >
            <ArrowLeftIcon className="h-4 w-4" />
            Back
          </button>
          <div className="flex items-center" style={{ gap: '12px' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onCancel}
            >
              Cancel
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={onSanitize}
              disabled={files.length === 0}
            >
              Next: Configure Mapping
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
