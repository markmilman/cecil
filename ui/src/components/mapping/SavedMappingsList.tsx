/**
 * SavedMappingsList component
 *
 * Displays a list of saved mapping configurations with view and delete actions.
 * Uses the useMappingList hook to fetch and manage mappings.
 */

import { useState } from 'react';
import { PencilIcon, TrashIcon, Loader2Icon, AlertCircleIcon, FileTextIcon, FolderOpenIcon } from 'lucide-react';
import { useMappingList } from '@/hooks/useMappingList';
import { apiClient } from '@/lib/apiClient';

import type { MappingConfigResponse } from '@/types';

interface SavedMappingsListProps {
  onViewMapping: (mapping: MappingConfigResponse) => void;
}

export function SavedMappingsList({ onViewMapping }: SavedMappingsListProps) {
  const { mappings, isLoading, error, deleteMappingById } = useMappingList();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleOpenFolder = async () => {
    try {
      await apiClient.openDirectory('~/.cecil/mappings/');
    } catch (err) {
      alert(`Failed to open folder: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleDelete = async (mapping: MappingConfigResponse) => {
    if (!window.confirm(`Delete mapping "${mapping.name}"? This action cannot be undone.`)) {
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
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '16px',
        }}
      >
        <h2
          style={{
            margin: 0,
            fontSize: '20px',
            color: 'var(--text-primary)',
            fontWeight: 600,
          }}
        >
          Saved Mappings
        </h2>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={handleOpenFolder}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '13px',
            padding: '6px 12px',
          }}
        >
          <FolderOpenIcon className="h-4 w-4" />
          Open Folder
        </button>
      </div>

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
                  marginBottom: '4px',
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
                  {mapping.name}
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
                <div
                  style={{
                    fontFamily: 'monospace',
                    fontSize: '11px',
                    color: 'var(--text-secondary)',
                  }}
                  title={mapping.mapping_id}
                >
                  ID: {mapping.mapping_id}
                </div>
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
                <PencilIcon className="h-4 w-4" />
                View / Edit
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
