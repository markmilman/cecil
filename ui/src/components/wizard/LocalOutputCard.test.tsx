import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LocalOutputCard } from './LocalOutputCard';

describe('LocalOutputCard', () => {
  it('renders the Local Output title', () => {
    render(<LocalOutputCard outputPath="/test/path/" />);
    expect(screen.getByText('Local Output')).toBeInTheDocument();
  });

  it('renders the "Files saved to:" label', () => {
    render(<LocalOutputCard outputPath="/test/path/" />);
    expect(screen.getByText('Files saved to:')).toBeInTheDocument();
  });

  it('renders the output path', () => {
    render(<LocalOutputCard outputPath="/Users/admin/cecil-output/" />);
    expect(screen.getByText('/Users/admin/cecil-output/')).toBeInTheDocument();
  });

  it('renders the Open Folder button', () => {
    render(<LocalOutputCard outputPath="/test/" />);
    expect(screen.getByText('Open Folder')).toBeInTheDocument();
  });

  it('calls onOpenFolder when button is clicked', () => {
    const onOpenFolder = vi.fn();
    render(<LocalOutputCard outputPath="/test/" onOpenFolder={onOpenFolder} />);
    fireEvent.click(screen.getByText('Open Folder'));
    expect(onOpenFolder).toHaveBeenCalledOnce();
  });
});
