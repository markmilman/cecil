import { FileSearchIcon } from 'lucide-react';

/**
 * Audit page component
 *
 * This page will eventually display sanitization results and redaction previews,
 * showing users what data was sanitized and how.
 */
export function AuditPage() {
  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <FileSearchIcon className="h-8 w-8 text-accent" />
            <h1 className="text-3xl font-bold text-primary">Audit View</h1>
          </div>
          <p className="text-muted">
            Review sanitization results and redaction previews
          </p>
        </div>

        {/* Placeholder Content */}
        <div className="bg-white border border-slate-200 rounded-lg p-12">
          <div className="text-center">
            <FileSearchIcon className="h-16 w-16 text-slate-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-primary mb-2">
              Audit Interface Coming Soon
            </h2>
            <p className="text-muted max-w-md mx-auto">
              This page will display sanitization results, showing which fields
              were redacted and providing previews of the sanitized data.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
