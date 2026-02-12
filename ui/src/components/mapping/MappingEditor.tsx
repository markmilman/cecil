/**
 * MappingEditor component
 *
 * Main container for the mapping editor interface. Uses the useMapping
 * hook for state management. Renders the toolbar, field mapping table,
 * and optional validation/preview panels.
 */

import { useState, useCallback } from 'react';
import { ArrowLeftIcon, AlertCircleIcon, Loader2Icon, ArrowRightIcon } from 'lucide-react';
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

  // Default name based on source filename
  const defaultName = source.split('/').pop()?.replace(/\.(jsonl|csv|parquet)$/i, '') || 'mapping';
  const [mappingName, setMappingName] = useState<string>(defaultName);

  const handleSave = useCallback(() => {
    save(mappingName.trim() || undefined);
  }, [save, mappingName]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <Loader2Icon className="h-8 w-8 text-indigo-600 animate-spin mb-3" />
        <p className="text-sm text-slate-500">
          Loading sample record from <span className="font-medium text-slate-700">{source}</span>...
        </p>
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
          className="flex items-center justify-between"
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
          <span>Mapping saved successfully.</span>
          {onMappingComplete && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => onMappingComplete(savedMappingId)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              Save &amp; Continue
              <ArrowRightIcon className="h-4 w-4" />
            </button>
          )}
        </div>
      )}

      {/* Name Input */}
      <div style={{ marginBottom: '16px' }}>
        <label
          htmlFor="mapping-name"
          style={{
            display: 'block',
            fontSize: '14px',
            fontWeight: 600,
            color: 'var(--text-primary)',
            marginBottom: '6px',
          }}
        >
          Mapping Name
        </label>
        <input
          id="mapping-name"
          type="text"
          value={mappingName}
          onChange={(e) => setMappingName(e.target.value)}
          placeholder="Enter a name for this mapping"
          style={{
            width: '100%',
            maxWidth: '400px',
            padding: '8px 12px',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            fontSize: '14px',
            color: 'var(--text-primary)',
            backgroundColor: 'var(--bg-card, white)',
            boxSizing: 'border-box',
          }}
        />
        <p
          style={{
            margin: '4px 0 0',
            fontSize: '12px',
            color: 'var(--text-secondary)',
          }}
        >
          Give this mapping a descriptive name to identify it later
        </p>
      </div>

      {/* Toolbar */}
      <MappingToolbar
        source={source}
        fieldCount={Object.keys(sampleRecord).length}
        defaultAction={defaultAction}
        onDefaultActionChange={setDefaultAction}
        onValidate={validate}
        onPreview={preview}
        onSave={handleSave}
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
