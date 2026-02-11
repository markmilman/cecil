/**
 * MappingPage component
 *
 * Displays the schema mapping interface. When a source is provided,
 * renders the MappingEditor. Otherwise shows the MappingEmptyState
 * guiding users to upload data first.
 */

import { MappingEditor } from '@/components/mapping/MappingEditor';
import { MappingEmptyState } from '@/components/mapping/MappingEmptyState';

interface MappingPageProps {
  source?: string | null;
  onStartWizard?: () => void;
  onBackToDashboard?: () => void;
  onMappingComplete?: (mappingId: string) => void;
}

export function MappingPage({
  source,
  onStartWizard,
  onBackToDashboard,
  onMappingComplete,
}: MappingPageProps) {
  if (source) {
    return (
      <MappingEditor
        source={source}
        onBackToDashboard={onBackToDashboard || (() => {})}
        onMappingComplete={onMappingComplete}
      />
    );
  }

  return (
    <MappingEmptyState onStartWizard={onStartWizard || (() => {})} />
  );
}
