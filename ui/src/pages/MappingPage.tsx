import { MapIcon } from 'lucide-react';

/**
 * Mapping page component
 *
 * This page will eventually contain the schema mapping interface where users
 * configure sanitization rules for their data sources.
 */
export function MappingPage() {
  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <MapIcon className="h-8 w-8 text-accent" />
            <h1 className="text-3xl font-bold text-primary">Schema Mapping</h1>
          </div>
          <p className="text-muted">
            Configure sanitization rules for your data sources
          </p>
        </div>

        {/* Placeholder Content */}
        <div className="bg-white border border-slate-200 rounded-lg p-12">
          <div className="text-center">
            <MapIcon className="h-16 w-16 text-slate-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-primary mb-2">
              Mapping Interface Coming Soon
            </h2>
            <p className="text-muted max-w-md mx-auto">
              This page will allow you to map data fields and configure
              sanitization actions (REDACT, MASK, HASH, KEEP).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
