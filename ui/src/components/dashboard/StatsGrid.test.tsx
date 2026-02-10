import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatsGrid } from './StatsGrid';

describe('StatsGrid', () => {
  it('renders three stat cards', () => {
    render(<StatsGrid />);
    expect(screen.getByText('Records Processed')).toBeInTheDocument();
    expect(screen.getByText('PII Redacted')).toBeInTheDocument();
    expect(screen.getByText('Est. Cost Savings')).toBeInTheDocument();
  });

  it('renders correct values', () => {
    render(<StatsGrid />);
    expect(screen.getByText('14,205')).toBeInTheDocument();
    expect(screen.getByText('1,892')).toBeInTheDocument();
    expect(screen.getByText('$4,200')).toBeInTheDocument();
  });

  it('renders the PII Redacted trend pill', () => {
    render(<StatsGrid />);
    expect(screen.getByText('13.2%')).toBeInTheDocument();
  });

  it('renders with a 3-column grid layout', () => {
    const { container } = render(<StatsGrid />);
    const grid = container.firstChild as HTMLElement;
    expect(grid.style.gridTemplateColumns).toBe('repeat(3, 1fr)');
  });
});
