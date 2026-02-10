import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { UploadZone } from './UploadZone';

describe('UploadZone', () => {
  it('renders the heading', () => {
    render(<UploadZone onBrowseFiles={vi.fn()} />);
    expect(screen.getByText('File Ingestion')).toBeInTheDocument();
  });

  it('renders the subtitle', () => {
    render(<UploadZone onBrowseFiles={vi.fn()} />);
    expect(screen.getByText('Select local files to sanitize. Data stays on your device.')).toBeInTheDocument();
  });

  it('renders the trust badge', () => {
    render(<UploadZone onBrowseFiles={vi.fn()} />);
    expect(screen.getByText('Data stays local')).toBeInTheDocument();
  });

  it('renders the drag and drop area', () => {
    render(<UploadZone onBrowseFiles={vi.fn()} />);
    expect(screen.getByText('Drag and drop log files')).toBeInTheDocument();
    expect(screen.getByText('Supported: JSONL, CSV, Parquet')).toBeInTheDocument();
  });

  it('renders the Browse Files button', () => {
    render(<UploadZone onBrowseFiles={vi.fn()} />);
    expect(screen.getByText('Browse Files')).toBeInTheDocument();
  });

  it('calls onBrowseFiles when Browse Files button is clicked', () => {
    const onBrowseFiles = vi.fn();
    render(<UploadZone onBrowseFiles={onBrowseFiles} />);
    fireEvent.click(screen.getByText('Browse Files'));
    expect(onBrowseFiles).toHaveBeenCalledOnce();
  });

  it('has an accessible upload zone with role button', () => {
    render(<UploadZone onBrowseFiles={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Browse files for upload' })).toBeInTheDocument();
  });

  it('calls onBrowseFiles on Enter key in upload zone', () => {
    const onBrowseFiles = vi.fn();
    render(<UploadZone onBrowseFiles={onBrowseFiles} />);
    const zone = screen.getByRole('button', { name: 'Browse files for upload' });
    fireEvent.keyDown(zone, { key: 'Enter' });
    expect(onBrowseFiles).toHaveBeenCalled();
  });
});
