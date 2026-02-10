import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CompletionView } from './CompletionView';

describe('CompletionView', () => {
  const defaultProps = {
    fileCount: 3,
    outputPath: '/Users/admin/downloads/cecil-output/',
    onBackToDashboard: vi.fn(),
  };

  it('renders the success heading', () => {
    render(<CompletionView {...defaultProps} />);
    expect(screen.getByText('Sanitization Complete')).toBeInTheDocument();
  });

  it('renders the file count subtitle for multiple files', () => {
    render(<CompletionView {...defaultProps} />);
    expect(screen.getByText('3 files have been processed and saved locally.')).toBeInTheDocument();
  });

  it('renders singular subtitle for one file', () => {
    render(<CompletionView {...defaultProps} fileCount={1} />);
    expect(screen.getByText('1 file has been processed and saved locally.')).toBeInTheDocument();
  });

  it('renders the Back to Dashboard button', () => {
    render(<CompletionView {...defaultProps} />);
    expect(screen.getByText('Back to Dashboard')).toBeInTheDocument();
  });

  it('calls onBackToDashboard when button is clicked', () => {
    const onBackToDashboard = vi.fn();
    render(<CompletionView {...defaultProps} onBackToDashboard={onBackToDashboard} />);
    fireEvent.click(screen.getByText('Back to Dashboard'));
    expect(onBackToDashboard).toHaveBeenCalledOnce();
  });

  it('renders the Local Output card with path', () => {
    render(<CompletionView {...defaultProps} />);
    expect(screen.getByText('Local Output')).toBeInTheDocument();
    expect(screen.getByText('Files saved to:')).toBeInTheDocument();
    expect(screen.getByText('/Users/admin/downloads/cecil-output/')).toBeInTheDocument();
  });

  it('renders the Open Folder button', () => {
    render(<CompletionView {...defaultProps} />);
    expect(screen.getByText('Open Folder')).toBeInTheDocument();
  });

  it('renders the CTA card with gradient content', () => {
    render(<CompletionView {...defaultProps} />);
    expect(screen.getByText('RECOMMENDED')).toBeInTheDocument();
    expect(screen.getByText('Unlock 20% Cost Savings')).toBeInTheDocument();
    expect(screen.getByText('Get Free Report')).toBeInTheDocument();
  });

  it('renders CTA value propositions', () => {
    render(<CompletionView {...defaultProps} />);
    expect(screen.getByText(/Detailed Spend Breakdown/)).toBeInTheDocument();
    expect(screen.getByText(/Token Efficiency Analysis/)).toBeInTheDocument();
  });

  it('renders the trust text', () => {
    render(<CompletionView {...defaultProps} />);
    expect(screen.getByText('Metadata only. No sensitive data.')).toBeInTheDocument();
  });
});
