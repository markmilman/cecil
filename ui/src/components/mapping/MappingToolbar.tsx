/**
 * MappingToolbar component
 *
 * Displays source information, a default action selector, and action
 * buttons for validate, preview, and save operations.
 */

import { FileTextIcon, CheckCircleIcon, EyeIcon, SaveIcon } from 'lucide-react';
import { ActionSelector } from './ActionSelector';

import type { RedactionAction } from '@/types';

interface MappingToolbarProps {
  source: string;
  fieldCount: number;
  defaultAction: RedactionAction;
  onDefaultActionChange: (action: RedactionAction) => void;
  onValidate: () => void;
  onPreview: () => void;
  onSave: () => void;
  isSaving: boolean;
  isValid?: boolean;
}

export function MappingToolbar({
  source,
  fieldCount,
  defaultAction,
  onDefaultActionChange,
  onValidate,
  onPreview,
  onSave,
  isSaving,
  isValid,
}: MappingToolbarProps) {
  const fileName = source.split('/').pop() || source;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: '8px',
        marginBottom: '16px',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      {/* Source info */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <FileTextIcon
            className="h-4 w-4"
            style={{ color: 'var(--text-secondary)' }}
          />
          <span
            className="font-mono"
            style={{
              fontSize: '13px',
              color: 'var(--text-primary)',
              fontWeight: 500,
            }}
            title={source}
          >
            {fileName}
          </span>
        </div>
        <span
          style={{
            fontSize: '12px',
            color: 'var(--text-secondary)',
            padding: '2px 8px',
            borderRadius: '4px',
            backgroundColor: 'var(--bg-subtle)',
          }}
        >
          {fieldCount} {fieldCount === 1 ? 'field' : 'fields'}
        </span>

        {/* Default action selector */}
        <div className="flex items-center gap-2">
          <span
            style={{
              fontSize: '12px',
              color: 'var(--text-secondary)',
              fontWeight: 500,
            }}
          >
            Default:
          </span>
          <ActionSelector value={defaultAction} onChange={onDefaultActionChange} />
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onValidate}
          style={{ fontSize: '13px', padding: '6px 12px' }}
        >
          <CheckCircleIcon className="h-4 w-4" />
          Validate
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onPreview}
          style={{ fontSize: '13px', padding: '6px 12px' }}
        >
          <EyeIcon className="h-4 w-4" />
          Preview
        </button>
        <button
          type="button"
          className="btn btn-primary"
          onClick={onSave}
          disabled={isSaving}
          style={{ fontSize: '13px', padding: '6px 12px' }}
        >
          <SaveIcon className="h-4 w-4" />
          {isSaving ? 'Saving...' : 'Save'}
          {isValid === true && (
            <CheckCircleIcon
              className="h-3 w-3"
              style={{ color: 'var(--success-color)', marginLeft: '2px' }}
            />
          )}
        </button>
      </div>
    </div>
  );
}
