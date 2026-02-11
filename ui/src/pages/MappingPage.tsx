import { MapIcon } from 'lucide-react';
import { EmptyState } from '@/components/common/EmptyState';

/**
 * Mapping page component
 *
 * Displays the schema mapping interface. Currently shows an empty state
 * guiding users to run a scan first.
 */
export function MappingPage() {
  return (
    <div className="p-10">
      <div className="max-w-6xl mx-auto">
        {/* Page Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <MapIcon className="h-8 w-8 text-accent" />
            <h1 className="text-3xl font-extrabold text-primary">Schema Mapping</h1>
          </div>
          <p className="text-muted leading-relaxed">
            Configure sanitization rules for your data sources
          </p>
        </div>

        {/* Empty State */}
        <EmptyState
          icon={<MapIcon />}
          title="No Active Scan"
          description="Run a scan on the Ingest page first, then return here to configure sanitization mappings for your data fields."
        />
      </div>
    </div>
  );
}
