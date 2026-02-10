import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LogOutput } from './LogOutput';

describe('LogOutput', () => {
  const lines = [
    '> Processing file.jsonl...',
    "> Found 'email' at line 42... [REDACTED]",
  ];

  it('renders all log lines', () => {
    render(<LogOutput lines={lines} />);
    expect(screen.getByText('> Processing file.jsonl...')).toBeInTheDocument();
    expect(screen.getByText("> Found 'email' at line 42... [REDACTED]")).toBeInTheDocument();
  });

  it('has role log for accessibility', () => {
    render(<LogOutput lines={lines} />);
    expect(screen.getByRole('log')).toBeInTheDocument();
  });

  it('has an accessible label', () => {
    render(<LogOutput lines={lines} />);
    expect(screen.getByRole('log')).toHaveAttribute('aria-label', 'Processing log');
  });

  it('renders empty state when no lines', () => {
    const { container } = render(<LogOutput lines={[]} />);
    const log = container.querySelector('[role="log"]');
    expect(log).toBeInTheDocument();
    expect(log?.children).toHaveLength(0);
  });
});
