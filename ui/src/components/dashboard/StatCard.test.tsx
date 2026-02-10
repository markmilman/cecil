import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatCard } from './StatCard';

describe('StatCard', () => {
  it('renders the label', () => {
    render(<StatCard label="Records Processed" value="14,205" />);
    expect(screen.getByText('Records Processed')).toBeInTheDocument();
  });

  it('renders the value', () => {
    render(<StatCard label="Records Processed" value="14,205" />);
    expect(screen.getByText('14,205')).toBeInTheDocument();
  });

  it('renders a trend pill when provided', () => {
    render(
      <StatCard
        label="PII Redacted"
        value="1,892"
        trend={{ label: '13.2%', direction: 'up' }}
      />,
    );
    expect(screen.getByText('13.2%')).toBeInTheDocument();
  });

  it('does not render a trend pill when not provided', () => {
    const { container } = render(
      <StatCard label="Records Processed" value="14,205" />,
    );
    expect(container.querySelectorAll('span')).toHaveLength(0);
  });

  it('renders ReactNode values', () => {
    render(
      <StatCard
        label="Cost"
        value={<><span data-testid="amount">$4,200</span>/mo</>}
      />,
    );
    expect(screen.getByTestId('amount')).toHaveTextContent('$4,200');
  });

  it('applies highlight styling when highlight is true', () => {
    const { container } = render(
      <StatCard label="Cost" value="$4,200" highlight />,
    );
    const card = container.firstChild as HTMLElement;
    expect(card.style.border).toContain('--primary-color');
  });

  it('applies default styling when highlight is not set', () => {
    const { container } = render(
      <StatCard label="Records" value="100" />,
    );
    const card = container.firstChild as HTMLElement;
    expect(card.style.border).toContain('--border-color');
  });
});
