import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FilePickerCard } from './FilePickerCard';

describe('FilePickerCard', () => {
  it('renders the file path input', () => {
    render(<FilePickerCard value="" onChange={() => {}} />);
    expect(screen.getByLabelText('File Path')).toBeInTheDocument();
  });

  it('displays the current value', () => {
    render(<FilePickerCard value="/data/test.jsonl" onChange={() => {}} />);
    expect(screen.getByDisplayValue('/data/test.jsonl')).toBeInTheDocument();
  });

  it('calls onChange when input changes', () => {
    const onChange = vi.fn();
    render(<FilePickerCard value="" onChange={onChange} />);
    fireEvent.change(screen.getByLabelText('File Path'), { target: { value: '/new/path.csv' } });
    expect(onChange).toHaveBeenCalledWith('/new/path.csv');
  });

  it('disables input when disabled prop is true', () => {
    render(<FilePickerCard value="" onChange={() => {}} disabled />);
    expect(screen.getByLabelText('File Path')).toBeDisabled();
  });
});
