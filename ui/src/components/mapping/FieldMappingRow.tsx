/**
 * FieldMappingRow component
 *
 * A single table row displaying a field name, its sample value,
 * an ActionSelector for choosing the redaction action, and an
 * optional preview of the transformed value.
 */

import { ActionSelector } from './ActionSelector';

import type { RedactionAction } from '@/types';

interface FieldMappingRowProps {
  fieldName: string;
  sampleValue: string;
  action: RedactionAction;
  previewValue?: string;
  onActionChange: (action: RedactionAction) => void;
}

export function FieldMappingRow({
  fieldName,
  sampleValue,
  action,
  previewValue,
  onActionChange,
}: FieldMappingRowProps) {
  return (
    <tr
      style={{
        borderBottom: '1px solid var(--border-color)',
        transition: 'background-color 0.15s',
      }}
    >
      <td
        className="font-mono"
        style={{
          padding: '10px 16px',
          fontSize: '13px',
          color: 'var(--text-primary)',
          fontWeight: 500,
        }}
      >
        {fieldName}
      </td>
      <td
        style={{
          padding: '10px 16px',
          fontSize: '13px',
          color: 'var(--text-secondary)',
          maxWidth: '200px',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
        title={sampleValue}
      >
        {sampleValue}
      </td>
      <td style={{ padding: '10px 16px' }}>
        <ActionSelector value={action} onChange={onActionChange} />
      </td>
      <td
        className="font-mono"
        style={{
          padding: '10px 16px',
          fontSize: '13px',
          color: previewValue !== undefined ? 'var(--text-primary)' : 'var(--text-faint)',
          maxWidth: '200px',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {previewValue !== undefined ? previewValue : '—'}
      </td>
    </tr>
  );
}
