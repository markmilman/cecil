/**
 * SavedMappingsList component
 *
 * Displays a list of saved mapping configurations with view and delete actions.
 * Uses the useMappingList hook to fetch and manage mappings.
 */

import { useState } from 'react';
import { EyeIcon, TrashIcon, Loader2Icon, AlertCircleIcon, FileTextIcon } from 'lucide-react';
import { useMappingList } from '@/hooks/useMappingList';

import type { MappingConfigResponse } from '@/types';

interface SavedMappingsListProps {
  onViewMapping: (mapping: MappingConfigResponse) => void;
}

export function SavedMappingsList({ onViewMapping }: SavedMappingsListProps) {
  const { mappings, isLoading, error, deleteMappingById } = useMappingList();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (mapping: MappingConfigResponse) => {
    if (!window.confirm(`Delete mapping ${mapping.mapping_id}? This action cannot be undone.`)) {
      return;
    }

    setDeletingId(mapping.mapping_id);
    try {
      await deleteMappingById(mapping.mapping_id);
    } finally {
      setDeletingId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Loader2Icon className="h-8 w-8 text-indigo-600 animate-spin mb-3" />
        <p className="text-sm text-slate-500">Loading saved mappings...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex items-center gap-2"
        style={{
          padding: '12px 16px',
          backgroundColor: 'var(--danger-bg)',
          border: '1px solid var(--danger-border)',
          borderRadius: '8px',
          color: 'var(--danger-color)',
          fontSize: '14px',
        }}
      >
        <AlertCircleIcon className="h-4 w-4" />
        {error}
      </div>
    );
  }

  if (mappings.length === 0) {
    return null;
  }

  return (
    <div>
      <h2
        style={{
          margin: '0 0 16px',
          fontSize: '20px',
          color: 'var(--text-primary)',
          fontWeight: 600,
        }}
      >
        Saved Mappings
      </h2>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {mappings.map((mapping) => (
          <div
            key={mapping.mapping_id}
            style={{
              padding: '16px',
              backgroundColor: 'white',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ flex: 1 }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '8px',
                }}
              >
                <FileTextIcon className="h-5 w-5 text-slate-400" />
                <h3
                  style={{
                    margin: 0,
                    fontSize: '16px',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                  }}
                >
                  {mapping.mapping_id}
                </h3>
              </div>

              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  fontSize: '14px',
                  color: 'var(--text-secondary)',
                }}
              >
                <div style={{ display: 'flex', gap: '16px' }}>
                  <span>{Object.keys(mapping.fields).length} field{Object.keys(mapping.fields).length !== 1 ? 's' : ''}</span>
                  <span>Default: {mapping.default_action}</span>
                  <span>{new Date(mapping.created_at).toLocaleDateString()}</span>
                </div>
                {mapping.yaml_path && (
                  <div
                    style={{
                      fontFamily: 'monospace',
                      fontSize: '12px',
                      color: 'var(--text-secondary)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                    title={mapping.yaml_path}
                  >
                    {mapping.yaml_path}
                  </div>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => onViewMapping(mapping)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <EyeIcon className="h-4 w-4" />
                View
              </button>

              <button
                type="button"
                className="btn btn-danger"
                onClick={() => handleDelete(mapping)}
                disabled={deletingId === mapping.mapping_id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                {deletingId === mapping.mapping_id ? (
                  <Loader2Icon className="h-4 w-4 animate-spin" />
                ) : (
                  <TrashIcon className="h-4 w-4" />
                )}
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
