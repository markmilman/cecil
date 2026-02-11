/**
 * MappingViewer component
 *
 * Displays a read-only view of a saved mapping configuration.
 * Shows field mappings, actions, and metadata.
 */

import { ArrowLeftIcon, FileTextIcon } from 'lucide-react';

import type { MappingConfigResponse } from '@/types';

interface MappingViewerProps {
  mapping: MappingConfigResponse;
  onBack: () => void;
}

export function MappingViewer({ mapping, onBack }: MappingViewerProps) {
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
            Mapping Configuration
          </h2>
          <p
            style={{
              margin: '4px 0 0',
              color: 'var(--text-secondary)',
              fontSize: '14px',
            }}
          >
            View saved mapping rules and field actions.
          </p>
        </div>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onBack}
        >
          <ArrowLeftIcon className="h-4 w-4" />
          Back
        </button>
      </div>

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
            {mapping.mapping_id}
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
            <span style={{ color: 'var(--text-secondary)' }}>Default Action:</span>{' '}
            <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
              {mapping.default_action}
            </span>
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
                  <span
                    style={{
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      fontWeight: 500,
                      backgroundColor:
                        fieldEntry.action === 'redact'
                          ? '#fef2f2'
                          : fieldEntry.action === 'mask'
                          ? '#fff7ed'
                          : fieldEntry.action === 'hash'
                          ? '#f3f4f6'
                          : '#f0fdf4',
                      color:
                        fieldEntry.action === 'redact'
                          ? '#991b1b'
                          : fieldEntry.action === 'mask'
                          ? '#9a3412'
                          : fieldEntry.action === 'hash'
                          ? '#374151'
                          : '#166534',
                    }}
                  >
                    {fieldEntry.action.toUpperCase()}
                  </span>
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
