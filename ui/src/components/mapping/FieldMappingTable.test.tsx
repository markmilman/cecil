import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FieldMappingTable } from './FieldMappingTable';
import { RedactionAction } from '@/types';

describe('FieldMappingTable', () => {
  const defaultFields = {
    email: 'john@example.com',
    name: 'John Doe',
    ip_address: '192.168.1.1',
  };

  const defaultActions = {
    email: RedactionAction.REDACT,
    name: RedactionAction.MASK,
    ip_address: RedactionAction.HASH,
  };

  it('renders the table header columns', () => {
    render(
      <FieldMappingTable
        fields={defaultFields}
        actions={defaultActions}
        onActionChange={vi.fn()}
      />,
    );
    expect(screen.getByText('Field Name')).toBeInTheDocument();
    expect(screen.getByText('Sample Value')).toBeInTheDocument();
    expect(screen.getByText('Action')).toBeInTheDocument();
    expect(screen.getByText('Preview')).toBeInTheDocument();
  });

  it('renders a row for each field', () => {
    render(
      <FieldMappingTable
        fields={defaultFields}
        actions={defaultActions}
        onActionChange={vi.fn()}
      />,
    );
    expect(screen.getByText('email')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
    expect(screen.getByText('name')).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('ip_address')).toBeInTheDocument();
    expect(screen.getByText('192.168.1.1')).toBeInTheDocument();
  });

  it('calls onActionChange with field name and new action', () => {
    const onActionChange = vi.fn();
    render(
      <FieldMappingTable
        fields={defaultFields}
        actions={defaultActions}
        onActionChange={onActionChange}
      />,
    );
    // Each row has an ActionSelector with 4 buttons. Click Keep on the first row.
    const keepButtons = screen.getAllByText('Keep');
    fireEvent.click(keepButtons[0]);
    expect(onActionChange).toHaveBeenCalledWith('email', RedactionAction.KEEP);
  });

  it('shows empty message when no fields are provided', () => {
    render(
      <FieldMappingTable
        fields={{}}
        actions={{}}
        onActionChange={vi.fn()}
      />,
    );
    expect(screen.getByText('No fields to display')).toBeInTheDocument();
  });

  it('renders preview values when provided', () => {
    const previews = {
      email: '[EMAIL_REDACTED]',
      name: 'J*** D**',
    };
    render(
      <FieldMappingTable
        fields={defaultFields}
        actions={defaultActions}
        previews={previews}
        onActionChange={vi.fn()}
      />,
    );
    expect(screen.getByText('[EMAIL_REDACTED]')).toBeInTheDocument();
    expect(screen.getByText('J*** D**')).toBeInTheDocument();
  });
});
