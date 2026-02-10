import { FileTextIcon, XIcon } from 'lucide-react';
import { WizardHeader } from './WizardHeader';
import { TrustBadge } from './TrustBadge';

/**
 * A file queued for sanitization
 */
export interface QueuedFile {
  name: string;
  size: string;
}

/**
 * Props for the QueuedFiles component
 */
interface QueuedFilesProps {
  files: QueuedFile[];
  onRemoveFile: (index: number) => void;
  onCancel: () => void;
  onSanitize: () => void;
}

/**
 * QueuedFiles component (Wizard Step 2)
 *
 * Shows a list of selected files with file icons, name/size,
 * and remove buttons. Includes Cancel and "Sanitize N Files"
 * action buttons in a footer.
 */
export function QueuedFiles({
  files,
  onRemoveFile,
  onCancel,
  onSanitize,
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
              key={`${file.name}-${index}`}
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
                    style={{
                      fontSize: '12px',
                      color: 'var(--text-secondary)',
                    }}
                  >
                    {file.size}
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
          className="flex items-center justify-end"
          style={{
            gap: '12px',
            borderTop: '1px solid var(--border-color)',
            paddingTop: '24px',
          }}
        >
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
            Sanitize {files.length} File{files.length !== 1 ? 's' : ''}
          </button>
        </div>
      </div>
    </div>
  );
}
