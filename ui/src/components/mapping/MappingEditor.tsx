/**
 * MappingEditor component
 *
 * Main container for the mapping editor interface. Uses the useMapping
 * hook for state management. Renders the toolbar, field mapping table,
 * and optional validation/preview panels.
 */

import { useEffect } from 'react';
import { ArrowLeftIcon, AlertCircleIcon } from 'lucide-react';
import { useMapping } from '@/hooks/useMapping';
import { MappingToolbar } from './MappingToolbar';
import { FieldMappingTable } from './FieldMappingTable';
import { ValidationPanel } from './ValidationPanel';
import { PreviewPanel } from './PreviewPanel';

interface MappingEditorProps {
  source: string;
  onBackToDashboard: () => void;
  onMappingComplete?: (mappingId: string) => void;
}

export function MappingEditor({ source, onBackToDashboard, onMappingComplete }: MappingEditorProps) {
  const {
    sampleRecord,
    fields,
    defaultAction,
    isLoading,
    error,
    validationResult,
    previewResult,
    isSaving,
    savedMappingId,
    setFieldAction,
    setDefaultAction,
    validate,
    preview,
    save,
    dismissValidation,
    dismissPreview,
  } = useMapping(source);

  // Auto-return to wizard after saving when onMappingComplete is provided
  useEffect(() => {
    if (savedMappingId && onMappingComplete) {
      onMappingComplete(savedMappingId);
    }
  }, [savedMappingId, onMappingComplete]);

  if (isLoading) {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '80px 0',
          color: 'var(--text-secondary)',
          fontSize: '14px',
        }}
      >
        Loading sample record...
      </div>
    );
  }

  const previewMap: Record<string, string> = {};
  for (const entry of previewResult) {
    previewMap[entry.field_name] = entry.transformed;
  }

  return (
    <div>
      {/* Header */}
      <div
        className="flex items-center justify-between"
        style={{ marginBottom: '24px' }}
      >
        <div>
          <h2
            style={{
              margin: 0,
              fontSize: '24px',
              color: 'var(--text-primary)',
              fontWeight: 700,
            }}
          >
            Configure Mapping Rules
          </h2>
          <p
            style={{
              margin: '4px 0 0',
              color: 'var(--text-secondary)',
              fontSize: '14px',
            }}
          >
            Assign sanitization actions to each field in your data source.
          </p>
        </div>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onBackToDashboard}
        >
          <ArrowLeftIcon className="h-4 w-4" />
          Back to Dashboard
        </button>
      </div>

      {/* Error banner */}
      {error && (
        <div
          className="flex items-center gap-2"
          style={{
            padding: '12px 16px',
            backgroundColor: 'var(--danger-bg)',
            border: '1px solid var(--danger-border)',
            borderRadius: '8px',
            marginBottom: '16px',
            color: 'var(--danger-color)',
            fontSize: '14px',
          }}
        >
          <AlertCircleIcon className="h-4 w-4" />
          {error}
        </div>
      )}

      {/* Success banner */}
      {savedMappingId && (
        <div
          className="flex items-center gap-2"
          style={{
            padding: '12px 16px',
            backgroundColor: 'var(--success-bg)',
            border: '1px solid var(--success-border)',
            borderRadius: '8px',
            marginBottom: '16px',
            color: 'var(--success-color)',
            fontSize: '14px',
          }}
        >
          Mapping saved successfully.
        </div>
      )}

      {/* Toolbar */}
      <MappingToolbar
        source={source}
        fieldCount={Object.keys(sampleRecord).length}
        defaultAction={defaultAction}
        onDefaultActionChange={setDefaultAction}
        onValidate={validate}
        onPreview={preview}
        onSave={save}
        isSaving={isSaving}
        isValid={validationResult?.is_valid}
      />

      {/* Field mapping table */}
      <FieldMappingTable
        fields={sampleRecord}
        actions={fields}
        previews={previewResult.length > 0 ? previewMap : undefined}
        onActionChange={setFieldAction}
      />

      {/* Validation panel */}
      <ValidationPanel result={validationResult} onClose={dismissValidation} />

      {/* Preview panel */}
      <PreviewPanel entries={previewResult} onClose={dismissPreview} />
    </div>
  );
}
