import { FileSearchIcon } from 'lucide-react';
import { EmptyState } from '@/components/common/EmptyState';

/**
 * Audit page component
 *
 * Displays sanitization results and redaction previews. Currently shows
 * an empty state guiding users to run a scan first.
 */
export function AuditPage() {
  return (
    <div className="p-10">
      <div className="max-w-6xl mx-auto">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <FileSearchIcon className="h-8 w-8 text-accent" />
            <h1 className="text-3xl font-extrabold text-primary">Audit View</h1>
          </div>
          <p className="text-slate-600 leading-relaxed">
            Review sanitization results and redaction previews
          </p>
        </div>

        {/* Empty State */}
        <EmptyState
          icon={<FileSearchIcon />}
          title="No Audit Results Yet"
          description="Complete a scan to view sanitization results. The audit view shows which fields were redacted and provides previews of the sanitized output."
          actionLabel="Start a Scan"
          actionHref="/ingest"
        />
      </div>
    </div>
  );
}
