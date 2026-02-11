import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MappingToolbar } from './MappingToolbar';
import { RedactionAction } from '@/types';

describe('MappingToolbar', () => {
  const defaultProps = {
    source: '/tmp/uploads/test-data.jsonl',
    fieldCount: 5,
    defaultAction: RedactionAction.REDACT,
    onDefaultActionChange: vi.fn(),
    onValidate: vi.fn(),
    onPreview: vi.fn(),
    onSave: vi.fn(),
    isSaving: false,
  };

  it('renders the source filename', () => {
    render(<MappingToolbar {...defaultProps} />);
    expect(screen.getByText('test-data.jsonl')).toBeInTheDocument();
  });

  it('renders the field count', () => {
    render(<MappingToolbar {...defaultProps} />);
    expect(screen.getByText('5 fields')).toBeInTheDocument();
  });

  it('renders singular field count', () => {
    render(<MappingToolbar {...defaultProps} fieldCount={1} />);
    expect(screen.getByText('1 field')).toBeInTheDocument();
  });

  it('renders Validate, Preview, and Save buttons', () => {
    render(<MappingToolbar {...defaultProps} />);
    expect(screen.getByText('Validate')).toBeInTheDocument();
    expect(screen.getByText('Preview')).toBeInTheDocument();
    expect(screen.getByText('Save')).toBeInTheDocument();
  });

  it('calls onValidate when Validate button is clicked', () => {
    const onValidate = vi.fn();
    render(<MappingToolbar {...defaultProps} onValidate={onValidate} />);
    fireEvent.click(screen.getByText('Validate'));
    expect(onValidate).toHaveBeenCalledOnce();
  });

  it('calls onPreview when Preview button is clicked', () => {
    const onPreview = vi.fn();
    render(<MappingToolbar {...defaultProps} onPreview={onPreview} />);
    fireEvent.click(screen.getByText('Preview'));
    expect(onPreview).toHaveBeenCalledOnce();
  });

  it('calls onSave when Save button is clicked', () => {
    const onSave = vi.fn();
    render(<MappingToolbar {...defaultProps} onSave={onSave} />);
    fireEvent.click(screen.getByText('Save'));
    expect(onSave).toHaveBeenCalledOnce();
  });

  it('shows Saving... text when isSaving is true', () => {
    render(<MappingToolbar {...defaultProps} isSaving={true} />);
    expect(screen.getByText('Saving...')).toBeInTheDocument();
  });
});
