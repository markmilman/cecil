/**
 * PreviewPanel component
 *
 * Displays a before/after comparison table for each field,
 * color-coded by the redaction action applied.
 */

import { XIcon } from 'lucide-react';
import { RedactionAction } from '@/types';

import type { FieldPreviewEntry } from '@/types';

interface PreviewPanelProps {
  entries: FieldPreviewEntry[];
  onClose: () => void;
}

const ACTION_COLORS: Record<RedactionAction, string> = {
  [RedactionAction.REDACT]: 'var(--danger-color)',
  [RedactionAction.MASK]: '#D97706',
  [RedactionAction.HASH]: 'var(--primary-color)',
  [RedactionAction.KEEP]: 'var(--success-color)',
};

export function PreviewPanel({ entries, onClose }: PreviewPanelProps) {
  if (entries.length === 0) return null;

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
          backgroundColor: 'var(--bg-subtle)',
        }}
      >
        <span
          style={{
            fontWeight: 600,
            fontSize: '14px',
            color: 'var(--text-primary)',
          }}
        >
          Mapping Preview
        </span>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close preview panel"
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

      {/* Preview table */}
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
            <th
              style={{
                padding: '8px 16px',
                textAlign: 'left',
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Field
            </th>
            <th
              style={{
                padding: '8px 16px',
                textAlign: 'left',
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Original
            </th>
            <th
              style={{
                padding: '8px 16px',
                textAlign: 'left',
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Transformed
            </th>
            <th
              style={{
                padding: '8px 16px',
                textAlign: 'left',
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Action
            </th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr
              key={entry.field_name}
              style={{ borderBottom: '1px solid var(--border-color)' }}
            >
              <td
                className="font-mono"
                style={{
                  padding: '8px 16px',
                  fontSize: '13px',
                  color: 'var(--text-primary)',
                  fontWeight: 500,
                }}
              >
                {entry.field_name}
              </td>
              <td
                style={{
                  padding: '8px 16px',
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  maxWidth: '200px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
                title={entry.original}
              >
                {entry.original}
              </td>
              <td
                className="font-mono"
                style={{
                  padding: '8px 16px',
                  fontSize: '13px',
                  color: ACTION_COLORS[entry.action],
                  fontWeight: 500,
                  maxWidth: '200px',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
                title={entry.transformed}
              >
                {entry.transformed}
              </td>
              <td
                style={{
                  padding: '8px 16px',
                  fontSize: '12px',
                  fontWeight: 600,
                  color: ACTION_COLORS[entry.action],
                  textTransform: 'uppercase',
                }}
              >
                {entry.action}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
