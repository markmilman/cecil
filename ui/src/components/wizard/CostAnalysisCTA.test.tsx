import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CostAnalysisCTA } from './CostAnalysisCTA';

describe('CostAnalysisCTA', () => {
  it('renders the RECOMMENDED label', () => {
    render(<CostAnalysisCTA />);
    expect(screen.getByText('RECOMMENDED')).toBeInTheDocument();
  });

  it('renders the title', () => {
    render(<CostAnalysisCTA />);
    expect(screen.getByText('Unlock 20% Cost Savings')).toBeInTheDocument();
  });

  it('renders the subtitle', () => {
    render(<CostAnalysisCTA />);
    expect(screen.getByText('Get a free report identifying model switching opportunities.')).toBeInTheDocument();
  });

  it('renders value propositions', () => {
    render(<CostAnalysisCTA />);
    expect(screen.getByText(/Detailed Spend Breakdown/)).toBeInTheDocument();
    expect(screen.getByText(/Token Efficiency Analysis/)).toBeInTheDocument();
  });

  it('renders the Get Free Report button', () => {
    render(<CostAnalysisCTA />);
    expect(screen.getByText('Get Free Report')).toBeInTheDocument();
  });

  it('calls onGetReport when button is clicked', () => {
    const onGetReport = vi.fn();
    render(<CostAnalysisCTA onGetReport={onGetReport} />);
    fireEvent.click(screen.getByText('Get Free Report'));
    expect(onGetReport).toHaveBeenCalledOnce();
  });

  it('renders the trust text', () => {
    render(<CostAnalysisCTA />);
    expect(screen.getByText('Metadata only. No sensitive data.')).toBeInTheDocument();
  });

  it('has gradient background styling', () => {
    const { container } = render(<CostAnalysisCTA />);
    const card = container.firstChild as HTMLElement;
    expect(card.style.background).toContain('linear-gradient');
  });
});
