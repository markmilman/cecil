import { CheckIcon, ArrowLeftIcon } from 'lucide-react';
import { LocalOutputCard } from './LocalOutputCard';
import { CostAnalysisCTA } from './CostAnalysisCTA';

interface CompletionViewProps {
  fileCount: number;
  outputPath: string;
  onBackToDashboard: () => void;
  onOpenFolder?: () => void;
  onViewResults?: () => void;
  onGetReport?: () => void;
  onBack: () => void;
  recordsProcessed?: number;
  recordsSanitized?: number;
}

/**
 * Wizard Step 5: Completion view.
 *
 * Shows a success header with green checkmark circle, "Sanitization
 * Complete" heading, subtitle with file/record count, and navigation buttons.
 * Below is a 2-column grid with LocalOutputCard (left) and
 * CostAnalysisCTA (right).
 */
export function CompletionView({
  fileCount,
  outputPath,
  onBackToDashboard,
  onOpenFolder,
  onViewResults,
  onGetReport,
  onBack,
  recordsProcessed,
  recordsSanitized,
}: CompletionViewProps) {
  return (
    <div>
      {/* Success Header */}
      <div
        className="flex items-center justify-between"
        style={{ marginBottom: '24px' }}
      >
        <div>
          <div className="flex items-center gap-3">
            <div
              className="flex items-center justify-center rounded-full"
              style={{
                width: '32px',
                height: '32px',
                backgroundColor: 'var(--success-bg)',
                color: 'var(--success-color)',
              }}
            >
              <CheckIcon className="h-5 w-5" strokeWidth={3} />
            </div>
            <h2
              style={{
                margin: 0,
                fontSize: '24px',
                color: 'var(--text-primary)',
              }}
            >
              Sanitization Complete
            </h2>
          </div>
          <p
            style={{
              margin: '4px 0 0 44px',
              color: 'var(--text-secondary)',
              fontSize: '14px',
            }}
          >
            {recordsProcessed !== undefined
              ? `${recordsProcessed} records processed, ${recordsSanitized ?? 0} sanitized.`
              : `${fileCount} ${fileCount === 1 ? 'file has' : 'files have'} been processed and saved locally.`
            }
          </p>
        </div>
        <div className="flex items-center" style={{ gap: '12px' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onBack}
          >
            <ArrowLeftIcon className="h-4 w-4" />
            Back
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onBackToDashboard}
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      {/* 2-column grid: Local Output + CTA */}
      <div
        style={{
          maxWidth: '800px',
          margin: '40px auto 0',
        }}
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '24px',
          }}
        >
          <LocalOutputCard
            outputPath={outputPath}
            onOpenFolder={onOpenFolder}
            onViewResults={onViewResults}
          />
          <CostAnalysisCTA
            onGetReport={onGetReport}
          />
        </div>
      </div>
    </div>
  );
}
