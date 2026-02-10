import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProgressCard } from './ProgressCard';

describe('ProgressCard', () => {
  it('renders the Running status pill', () => {
    render(<ProgressCard percentComplete={50} recordCount={1000} elapsedSeconds={12} />);
    expect(screen.getByText('Running')).toBeInTheDocument();
  });

  it('renders the elapsed time formatted as MM:SS', () => {
    render(<ProgressCard percentComplete={50} recordCount={1000} elapsedSeconds={72} />);
    expect(screen.getByText('01:12')).toBeInTheDocument();
  });

  it('renders zero elapsed time correctly', () => {
    render(<ProgressCard percentComplete={0} recordCount={0} elapsedSeconds={0} />);
    expect(screen.getByText('00:00')).toBeInTheDocument();
  });

  it('renders the record count', () => {
    render(<ProgressCard percentComplete={50} recordCount={1500} elapsedSeconds={10} />);
    expect(screen.getByText('1,500 records sanitized')).toBeInTheDocument();
  });

  it('renders the Live indicator', () => {
    render(<ProgressCard percentComplete={50} recordCount={1000} elapsedSeconds={10} />);
    expect(screen.getByText('Live')).toBeInTheDocument();
  });

  it('renders a progress bar with role progressbar', () => {
    render(<ProgressCard percentComplete={42} recordCount={500} elapsedSeconds={5} />);
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toBeInTheDocument();
    expect(progressbar).toHaveAttribute('aria-valuenow', '42');
    expect(progressbar).toHaveAttribute('aria-valuemin', '0');
    expect(progressbar).toHaveAttribute('aria-valuemax', '100');
  });

  it('has an accessible label on the progress bar', () => {
    render(<ProgressCard percentComplete={50} recordCount={500} elapsedSeconds={5} />);
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-label', 'Sanitization progress');
  });
});
