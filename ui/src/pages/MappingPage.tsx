/**
 * MappingPage component
 *
 * Displays the schema mapping interface. When a source is provided,
 * renders the MappingEditor. Otherwise shows the MappingEmptyState
 * guiding users to upload data first, along with a list of saved mappings.
 */

import { useState } from 'react';
import { MappingEditor } from '@/components/mapping/MappingEditor';
import { MappingEmptyState } from '@/components/mapping/MappingEmptyState';
import { SavedMappingsList } from '@/components/mapping/SavedMappingsList';
import { MappingViewer } from '@/components/mapping/MappingViewer';

import type { MappingConfigResponse } from '@/types';

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
  const [viewingMapping, setViewingMapping] = useState<MappingConfigResponse | null>(null);

  if (source) {
    return (
      <MappingEditor
        source={source}
        onBackToDashboard={onBackToDashboard || (() => {})}
        onMappingComplete={onMappingComplete}
      />
    );
  }

  if (viewingMapping) {
    return (
      <MappingViewer
        mapping={viewingMapping}
        onBack={() => setViewingMapping(null)}
      />
    );
  }

  return (
    <div>
      <MappingEmptyState onStartWizard={onStartWizard || (() => {})} />

      <div style={{ marginTop: '32px' }}>
        <SavedMappingsList onViewMapping={setViewingMapping} />
      </div>
    </div>
  );
}
