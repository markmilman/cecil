import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FormatSelector } from './FormatSelector';
import { FileFormat } from '@/types';

describe('FormatSelector', () => {
  it('renders all format options', () => {
    render(<FormatSelector value={null} onChange={() => {}} />);
    expect(screen.getByText('Auto-detect')).toBeInTheDocument();
    expect(screen.getByText('JSONL')).toBeInTheDocument();
    expect(screen.getByText('CSV')).toBeInTheDocument();
    expect(screen.getByText('Parquet')).toBeInTheDocument();
  });

  it('calls onChange when a format is selected', () => {
    const onChange = vi.fn();
    render(<FormatSelector value={null} onChange={onChange} />);
    fireEvent.click(screen.getByText('JSONL'));
    expect(onChange).toHaveBeenCalledWith(FileFormat.JSONL);
  });

  it('shows auto-detect as selected by default', () => {
    render(<FormatSelector value={null} onChange={() => {}} />);
    const autoRadio = screen.getByRole('radio', { name: /auto-detect/i });
    expect(autoRadio).toBeChecked();
  });
});
