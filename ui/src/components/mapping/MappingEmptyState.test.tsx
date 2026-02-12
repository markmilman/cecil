import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MappingEmptyState } from './MappingEmptyState';

describe('MappingEmptyState', () => {
  it('renders the empty state title and description', () => {
    render(<MappingEmptyState onStartWizard={vi.fn()} />);
    expect(screen.getByText('No Data Source Selected')).toBeInTheDocument();
    expect(
      screen.getByText('Upload a data file first, then configure sanitization mapping rules for each field.'),
    ).toBeInTheDocument();
  });

  it('renders the Upload Data File button', () => {
    render(<MappingEmptyState onStartWizard={vi.fn()} />);
    expect(screen.getByText('Upload Data File')).toBeInTheDocument();
  });

  it('calls onStartWizard when the CTA is clicked', () => {
    const onStartWizard = vi.fn();
    render(<MappingEmptyState onStartWizard={onStartWizard} />);
    fireEvent.click(screen.getByText('Upload Data File'));
    expect(onStartWizard).toHaveBeenCalledOnce();
  });
});
