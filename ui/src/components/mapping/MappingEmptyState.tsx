/**
 * MappingEmptyState component
 *
 * Displayed when no data source has been selected for mapping.
 * Uses the shared EmptyState component with a CTA to start the wizard.
 */

import { MapIcon } from 'lucide-react';
import { EmptyState } from '@/components/common/EmptyState';

interface MappingEmptyStateProps {
  onStartWizard: () => void;
}

export function MappingEmptyState({ onStartWizard }: MappingEmptyStateProps) {
  return (
    <EmptyState
      icon={<MapIcon />}
      title="No Data Source Selected"
      description="Upload a data file first, then configure sanitization mapping rules for each field."
      actionLabel="Upload Data File"
      onAction={onStartWizard}
    />
  );
}
