/**
 * FieldMappingTable component
 *
 * Renders a table of fields with their sample values, action selectors,
 * and optional preview values. Delegates each row to FieldMappingRow.
 */

import { FieldMappingRow } from './FieldMappingRow';

import type { RedactionAction } from '@/types';

interface FieldMappingTableProps {
  fields: Record<string, string>;
  actions: Record<string, RedactionAction>;
  previews?: Record<string, string>;
  onActionChange: (fieldName: string, action: RedactionAction) => void;
}

export function FieldMappingTable({
  fields,
  actions,
  previews,
  onActionChange,
}: FieldMappingTableProps) {
  const fieldNames = Object.keys(fields);

  if (fieldNames.length === 0) {
    return (
      <div
        style={{
          padding: '40px',
          textAlign: 'center',
          color: 'var(--text-secondary)',
          fontSize: '14px',
        }}
      >
        No fields to display
      </div>
    );
  }

  return (
    <div
      style={{
        border: '1px solid var(--border-color)',
        borderRadius: '8px',
        overflow: 'hidden',
        backgroundColor: 'var(--bg-card)',
      }}
    >
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr
            style={{
              borderBottom: '2px solid var(--border-color)',
              backgroundColor: 'var(--bg-subtle)',
            }}
          >
            <th
              style={{
                padding: '10px 16px',
                textAlign: 'left',
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Field Name
            </th>
            <th
              style={{
                padding: '10px 16px',
                textAlign: 'left',
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Sample Value
            </th>
            <th
              style={{
                padding: '10px 16px',
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
            <th
              style={{
                padding: '10px 16px',
                textAlign: 'left',
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Preview
            </th>
          </tr>
        </thead>
        <tbody>
          {fieldNames.map((fieldName) => (
            <FieldMappingRow
              key={fieldName}
              fieldName={fieldName}
              sampleValue={fields[fieldName]}
              action={actions[fieldName]}
              previewValue={previews?.[fieldName]}
              onActionChange={(action) => onActionChange(fieldName, action)}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
