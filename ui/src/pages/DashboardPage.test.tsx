import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DashboardPage } from './DashboardPage';

describe('DashboardPage', () => {
  it('renders the page heading', () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    expect(screen.getByText('Audit Dashboard')).toBeInTheDocument();
  });

  it('renders the subtitle', () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    expect(screen.getByText('Overview of recent sanitization jobs and PII detection.')).toBeInTheDocument();
  });

  it('renders the New Sanitization Job button', () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    expect(screen.getByText('New Sanitization Job')).toBeInTheDocument();
  });

  it('calls onStartWizard when button is clicked', () => {
    const onStartWizard = vi.fn();
    render(<DashboardPage onStartWizard={onStartWizard} />);
    fireEvent.click(screen.getByText('New Sanitization Job'));
    expect(onStartWizard).toHaveBeenCalledOnce();
  });

  it('renders the Records Processed stat', () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    expect(screen.getByText('Records Processed')).toBeInTheDocument();
    expect(screen.getByText('14,205')).toBeInTheDocument();
  });

  it('renders the PII Redacted stat with trend pill', () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    expect(screen.getByText('PII Redacted')).toBeInTheDocument();
    expect(screen.getByText('1,892')).toBeInTheDocument();
    expect(screen.getByText('13.2%')).toBeInTheDocument();
  });

  it('renders the Est. Cost Savings stat', () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    expect(screen.getByText('Est. Cost Savings')).toBeInTheDocument();
    expect(screen.getByText('$4,200')).toBeInTheDocument();
  });

  it('renders the job history table header', () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    expect(screen.getByText('Job ID')).toBeInTheDocument();
    expect(screen.getByText('Source')).toBeInTheDocument();
    expect(screen.getByText('Date')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Action')).toBeInTheDocument();
  });

  it('renders job history rows with status pills', () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    expect(screen.getByText('local-job-003')).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('local-job-002')).toBeInTheDocument();
    expect(screen.getByText('PII Detected')).toBeInTheDocument();
  });

  it('renders action buttons in job rows', () => {
    render(<DashboardPage onStartWizard={vi.fn()} />);
    expect(screen.getByText('View Report')).toBeInTheDocument();
    expect(screen.getByText('Review')).toBeInTheDocument();
  });
});
