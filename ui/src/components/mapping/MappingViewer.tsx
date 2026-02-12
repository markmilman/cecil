/**
 * MappingViewer component
 *
 * Displays an editable view of a saved mapping configuration.
 * Allows editing the name, default action, and per-field actions.
 */

import { useState } from 'react';
import { ArrowLeftIcon, FileTextIcon, SaveIcon, CheckCircleIcon } from 'lucide-react';

import { ActionSelector } from '@/components/mapping/ActionSelector';
import { apiClient } from '@/lib/apiClient';
import { RedactionAction } from '@/types';

import type { MappingConfigResponse, FieldMappingEntry } from '@/types';

interface MappingViewerProps {
  mapping: MappingConfigResponse;
  onBack: () => void;
  onSaved?: () => void;
}

export function MappingViewer({ mapping, onBack, onSaved }: MappingViewerProps) {
  const [editedName, setEditedName] = useState(mapping.name);
  const [editedDefaultAction, setEditedDefaultAction] = useState<RedactionAction>(
    mapping.default_action as unknown as RedactionAction,
  );
  const [editedActions, setEditedActions] = useState<Record<string, RedactionAction>>(() => {
    const actions: Record<string, RedactionAction> = {};
    for (const [fieldName, fieldEntry] of Object.entries(mapping.fields)) {
      actions[fieldName] = fieldEntry.action as unknown as RedactionAction;
    }
    return actions;
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const hasChanges =
    editedName !== mapping.name ||
    editedDefaultAction !== (mapping.default_action as unknown as RedactionAction) ||
    Object.entries(editedActions).some(([fieldName, action]) => {
      const originalAction = mapping.fields[fieldName]?.action as unknown as RedactionAction;
      return action !== originalAction;
    });

  const handleActionChange = (fieldName: string, action: RedactionAction) => {
    setEditedActions((prev) => ({ ...prev, [fieldName]: action }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      const fields: Record<string, FieldMappingEntry> = {};
      for (const [fieldName, action] of Object.entries(editedActions)) {
        fields[fieldName] = {
          action,
          options: mapping.fields[fieldName]?.options || {},
        };
      }

      await apiClient.updateMapping(mapping.mapping_id, {
        version: mapping.version,
        default_action: editedDefaultAction,
        fields,
        name: editedName,
      });

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);

      if (onSaved) {
        onSaved();
      }
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : 'Failed to save changes');
    } finally {
      setIsSaving(false);
    }
  };
  return (
    <div>
      {/* Header */}
      <div
        className="flex items-center justify-between"
        style={{ marginBottom: '24px' }}
      >
        <div style={{ flex: 1, marginRight: '16px' }}>
          <input
            type="text"
            value={editedName}
            onChange={(e) => setEditedName(e.target.value)}
            style={{
              fontSize: '24px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              border: '1px solid var(--border-color)',
              borderRadius: '4px',
              padding: '4px 8px',
              width: '100%',
              maxWidth: '500px',
            }}
          />
          <p
            style={{
              margin: '4px 0 0',
              color: 'var(--text-secondary)',
              fontSize: '14px',
            }}
          >
            Edit mapping name, default action, and field actions.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleSave}
            disabled={!hasChanges || isSaving}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            {saveSuccess ? (
              <>
                <CheckCircleIcon className="h-4 w-4" />
                Saved
              </>
            ) : (
              <>
                <SaveIcon className="h-4 w-4" />
                {isSaving ? 'Saving...' : 'Save Changes'}
              </>
            )}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onBack}
          >
            <ArrowLeftIcon className="h-4 w-4" />
            Back
          </button>
        </div>
      </div>

      {saveError && (
        <div
          style={{
            padding: '12px 16px',
            backgroundColor: 'var(--danger-bg)',
            border: '1px solid var(--danger-border)',
            borderRadius: '8px',
            color: 'var(--danger-color)',
            fontSize: '14px',
            marginBottom: '16px',
          }}
        >
          {saveError}
        </div>
      )}

      {/* Mapping metadata */}
      <div
        style={{
          padding: '16px',
          backgroundColor: 'var(--bg-subtle)',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          marginBottom: '24px',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '12px',
          }}
        >
          <FileTextIcon className="h-5 w-5 text-indigo-600" />
          <h3
            style={{
              margin: 0,
              fontSize: '16px',
              fontWeight: 600,
              color: 'var(--text-primary)',
            }}
          >
            Mapping Details
          </h3>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '12px',
            fontSize: '14px',
          }}
        >
          <div>
            <span style={{ color: 'var(--text-secondary)' }}>Mapping ID:</span>{' '}
            <span
              style={{
                fontWeight: 500,
                color: 'var(--text-primary)',
                fontFamily: 'monospace',
                fontSize: '12px',
              }}
              title={mapping.mapping_id}
            >
              {mapping.mapping_id}
            </span>
          </div>
          <div>
            <span
              style={{
                color: 'var(--text-secondary)',
                display: 'block',
                marginBottom: '4px',
              }}
            >
              Default Action:
            </span>
            <ActionSelector
              value={editedDefaultAction}
              onChange={setEditedDefaultAction}
            />
          </div>
          <div>
            <span style={{ color: 'var(--text-secondary)' }}>Fields:</span>{' '}
            <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
              {Object.keys(mapping.fields).length}
            </span>
          </div>
          <div>
            <span style={{ color: 'var(--text-secondary)' }}>Created:</span>{' '}
            <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
              {new Date(mapping.created_at).toLocaleString()}
            </span>
          </div>
          <div>
            <span style={{ color: 'var(--text-secondary)' }}>Policy Hash:</span>{' '}
            <span
              style={{
                fontWeight: 500,
                color: 'var(--text-primary)',
                fontFamily: 'monospace',
                fontSize: '12px',
              }}
            >
              {mapping.policy_hash.substring(0, 12)}...
            </span>
          </div>
          {mapping.yaml_path && (
            <div style={{ gridColumn: '1 / -1' }}>
              <span style={{ color: 'var(--text-secondary)' }}>YAML Path:</span>{' '}
              <span
                style={{
                  fontWeight: 500,
                  color: 'var(--text-primary)',
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  wordBreak: 'break-all',
                }}
                title={mapping.yaml_path}
              >
                {mapping.yaml_path}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Field mappings table */}
      <div
        style={{
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          overflow: 'hidden',
        }}
      >
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
          }}
        >
          <thead
            style={{
              backgroundColor: 'var(--bg-subtle)',
            }}
          >
            <tr>
              <th
                style={{
                  textAlign: 'left',
                  padding: '12px 16px',
                  fontSize: '12px',
                  fontWeight: 600,
                  color: 'var(--text-secondary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  borderBottom: '1px solid var(--border-color)',
                }}
              >
                Field Name
              </th>
              <th
                style={{
                  textAlign: 'left',
                  padding: '12px 16px',
                  fontSize: '12px',
                  fontWeight: 600,
                  color: 'var(--text-secondary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  borderBottom: '1px solid var(--border-color)',
                }}
              >
                Action
              </th>
              <th
                style={{
                  textAlign: 'left',
                  padding: '12px 16px',
                  fontSize: '12px',
                  fontWeight: 600,
                  color: 'var(--text-secondary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  borderBottom: '1px solid var(--border-color)',
                }}
              >
                Options
              </th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(mapping.fields).map(([fieldName, fieldEntry], index) => (
              <tr
                key={fieldName}
                style={{
                  borderBottom:
                    index < Object.keys(mapping.fields).length - 1
                      ? '1px solid var(--border-color)'
                      : 'none',
                  backgroundColor: index % 2 === 0 ? 'white' : 'var(--bg-secondary)',
                }}
              >
                <td
                  style={{
                    padding: '12px 16px',
                    fontSize: '14px',
                    color: 'var(--text-primary)',
                    fontFamily: 'monospace',
                  }}
                >
                  {fieldName}
                </td>
                <td
                  style={{
                    padding: '12px 16px',
                    fontSize: '14px',
                  }}
                >
                  <ActionSelector
                    value={editedActions[fieldName]}
                    onChange={(action) => handleActionChange(fieldName, action)}
                  />
                </td>
                <td
                  style={{
                    padding: '12px 16px',
                    fontSize: '13px',
                    color: 'var(--text-secondary)',
                    fontFamily: 'monospace',
                  }}
                >
                  {Object.keys(fieldEntry.options).length > 0
                    ? JSON.stringify(fieldEntry.options)
                    : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
