import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProcessingView } from './ProcessingView';

describe('ProcessingView', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders the heading', () => {
    render(<ProcessingView onComplete={vi.fn()} onStop={vi.fn()} />);
    expect(screen.getByText('Sanitizing Files...')).toBeInTheDocument();
  });

  it('renders the subtitle', () => {
    render(<ProcessingView onComplete={vi.fn()} onStop={vi.fn()} />);
    expect(screen.getByText('Please wait while we scrub PII locally.')).toBeInTheDocument();
  });

  it('renders the Stop Process button', () => {
    render(<ProcessingView onComplete={vi.fn()} onStop={vi.fn()} />);
    expect(screen.getByText('Stop Process')).toBeInTheDocument();
  });

  it('renders the Running status pill', () => {
    render(<ProcessingView onComplete={vi.fn()} onStop={vi.fn()} />);
    expect(screen.getByText('Running')).toBeInTheDocument();
  });

  it('renders a progress bar with role progressbar', () => {
    render(<ProcessingView onComplete={vi.fn()} onStop={vi.fn()} />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders the Live indicator', () => {
    render(<ProcessingView onComplete={vi.fn()} onStop={vi.fn()} />);
    expect(screen.getByText('Live')).toBeInTheDocument();
  });

  it('renders log output lines', () => {
    render(<ProcessingView onComplete={vi.fn()} onStop={vi.fn()} />);
    expect(screen.getByText('> Processing app-logs-prod.jsonl...')).toBeInTheDocument();
  });

  it('has an accessible log area', () => {
    render(<ProcessingView onComplete={vi.fn()} onStop={vi.fn()} />);
    expect(screen.getByRole('log')).toBeInTheDocument();
  });

  it('calls onStop when Stop Process is clicked', () => {
    const onStop = vi.fn();
    render(<ProcessingView onComplete={vi.fn()} onStop={onStop} />);
    screen.getByText('Stop Process').click();
    expect(onStop).toHaveBeenCalledOnce();
  });
});
