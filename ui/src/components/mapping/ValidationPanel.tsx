/**
 * ValidationPanel component
 *
 * Displays the result of mapping validation with color-coded lists
 * of matched, unmapped, and missing fields.
 */

import { XIcon, CheckCircleIcon, AlertTriangleIcon, XCircleIcon } from 'lucide-react';

import type { MappingValidationResult } from '@/types';

interface ValidationPanelProps {
  result: MappingValidationResult | null;
  onClose: () => void;
}

export function ValidationPanel({ result, onClose }: ValidationPanelProps) {
  if (!result) return null;

  return (
    <div
      style={{
        border: '1px solid var(--border-color)',
        borderRadius: '8px',
        backgroundColor: 'var(--bg-card)',
        marginTop: '16px',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between"
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid var(--border-color)',
          backgroundColor: result.is_valid ? 'var(--success-bg)' : 'var(--danger-bg)',
        }}
      >
        <div className="flex items-center gap-2">
          {result.is_valid ? (
            <CheckCircleIcon className="h-5 w-5" style={{ color: 'var(--success-color)' }} />
          ) : (
            <AlertTriangleIcon className="h-5 w-5" style={{ color: 'var(--danger-color)' }} />
          )}
          <span
            style={{
              fontWeight: 600,
              fontSize: '14px',
              color: 'var(--text-primary)',
            }}
          >
            {result.is_valid ? 'Mapping is Valid' : 'Mapping Has Issues'}
          </span>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close validation panel"
          style={{
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            padding: '4px',
            color: 'var(--text-secondary)',
          }}
        >
          <XIcon className="h-4 w-4" />
        </button>
      </div>

      {/* Field lists */}
      <div style={{ padding: '16px', display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
        {/* Matched fields */}
        {result.matched_fields.length > 0 && (
          <div style={{ minWidth: '150px' }}>
            <div
              className="flex items-center gap-1"
              style={{ marginBottom: '8px' }}
            >
              <CheckCircleIcon className="h-4 w-4" style={{ color: 'var(--success-color)' }} />
              <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--success-color)' }}>
                Matched ({result.matched_fields.length})
              </span>
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {result.matched_fields.map((field) => (
                <li
                  key={field}
                  className="font-mono"
                  style={{ fontSize: '12px', color: 'var(--text-primary)', padding: '2px 0' }}
                >
                  {field}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Unmapped fields */}
        {result.unmapped_fields.length > 0 && (
          <div style={{ minWidth: '150px' }}>
            <div
              className="flex items-center gap-1"
              style={{ marginBottom: '8px' }}
            >
              <AlertTriangleIcon className="h-4 w-4" style={{ color: '#D97706' }} />
              <span style={{ fontSize: '12px', fontWeight: 600, color: '#D97706' }}>
                Unmapped ({result.unmapped_fields.length})
              </span>
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {result.unmapped_fields.map((field) => (
                <li
                  key={field}
                  className="font-mono"
                  style={{ fontSize: '12px', color: 'var(--text-primary)', padding: '2px 0' }}
                >
                  {field}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Missing fields */}
        {result.missing_fields.length > 0 && (
          <div style={{ minWidth: '150px' }}>
            <div
              className="flex items-center gap-1"
              style={{ marginBottom: '8px' }}
            >
              <XCircleIcon className="h-4 w-4" style={{ color: 'var(--danger-color)' }} />
              <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--danger-color)' }}>
                Missing ({result.missing_fields.length})
              </span>
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {result.missing_fields.map((field) => (
                <li
                  key={field}
                  className="font-mono"
                  style={{ fontSize: '12px', color: 'var(--text-primary)', padding: '2px 0' }}
                >
                  {field}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
