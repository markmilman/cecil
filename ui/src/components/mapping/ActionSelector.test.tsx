import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ActionSelector } from './ActionSelector';
import { RedactionAction } from '@/types';

describe('ActionSelector', () => {
  it('renders all four action buttons', () => {
    render(<ActionSelector value={RedactionAction.REDACT} onChange={vi.fn()} />);
    expect(screen.getByText('Redact')).toBeInTheDocument();
    expect(screen.getByText('Mask')).toBeInTheDocument();
    expect(screen.getByText('Hash')).toBeInTheDocument();
    expect(screen.getByText('Keep')).toBeInTheDocument();
  });

  it('marks the active action with aria-pressed', () => {
    render(<ActionSelector value={RedactionAction.MASK} onChange={vi.fn()} />);
    expect(screen.getByText('Mask')).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText('Redact')).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByText('Hash')).toHaveAttribute('aria-pressed', 'false');
    expect(screen.getByText('Keep')).toHaveAttribute('aria-pressed', 'false');
  });

  it('calls onChange with the correct action when a button is clicked', () => {
    const onChange = vi.fn();
    render(<ActionSelector value={RedactionAction.REDACT} onChange={onChange} />);
    fireEvent.click(screen.getByText('Keep'));
    expect(onChange).toHaveBeenCalledWith(RedactionAction.KEEP);
  });

  it('calls onChange with HASH when Hash button is clicked', () => {
    const onChange = vi.fn();
    render(<ActionSelector value={RedactionAction.REDACT} onChange={onChange} />);
    fireEvent.click(screen.getByText('Hash'));
    expect(onChange).toHaveBeenCalledWith(RedactionAction.HASH);
  });

  it('disables all buttons when disabled prop is true', () => {
    render(<ActionSelector value={RedactionAction.REDACT} onChange={vi.fn()} disabled />);
    const buttons = screen.getAllByRole('button');
    for (const button of buttons) {
      expect(button).toBeDisabled();
    }
  });

  it('has a group role with an aria-label', () => {
    render(<ActionSelector value={RedactionAction.REDACT} onChange={vi.fn()} />);
    expect(screen.getByRole('group')).toHaveAttribute('aria-label', 'Redaction action');
  });
});
