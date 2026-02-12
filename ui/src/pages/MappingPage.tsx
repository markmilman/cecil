/**
 * MappingPage component
 *
 * Displays the schema mapping interface. When a source is provided,
 * renders the MappingEditor. Otherwise shows the MappingEmptyState
 * guiding users to upload data first, along with a list of saved mappings.
 */

import { useState, useCallback, useEffect } from 'react';
import { MappingEditor } from '@/components/mapping/MappingEditor';
import { MappingEmptyState } from '@/components/mapping/MappingEmptyState';
import { SavedMappingsList } from '@/components/mapping/SavedMappingsList';
import { MappingViewer } from '@/components/mapping/MappingViewer';
import { apiClient } from '@/lib/apiClient';

import type { MappingConfigResponse } from '@/types';

interface MappingPageProps {
  source?: string | null;
  onStartWizard?: () => void;
  onBackToDashboard?: () => void;
  onMappingComplete?: (mappingId: string) => void;
  initialMappingId?: string | null;
}

export function MappingPage({
  source,
  onStartWizard,
  onBackToDashboard,
  onMappingComplete,
  initialMappingId,
}: MappingPageProps) {
  const [viewingMapping, setViewingMapping] = useState<MappingConfigResponse | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    if (initialMappingId) {
      apiClient.getMapping(initialMappingId).then(setViewingMapping).catch(() => {
        // Mapping may have been deleted; ignore
      });
    }
  }, [initialMappingId]);

  const handleMappingSaved = useCallback(() => {
    setRefreshKey((prev) => prev + 1);
  }, []);

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
        onSaved={handleMappingSaved}
      />
    );
  }

  return (
    <div>
      <MappingEmptyState onStartWizard={onStartWizard || (() => {})} />

      <div style={{ marginTop: '32px' }}>
        <SavedMappingsList key={refreshKey} onViewMapping={setViewingMapping} />
      </div>
    </div>
  );
}
