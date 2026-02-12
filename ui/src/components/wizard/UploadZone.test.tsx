import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
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

  it('has an accessible upload zone with role button', () => {
    render(<UploadZone onBrowseFiles={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Browse files for upload' })).toBeInTheDocument();
  });

  it('shows uploading state', () => {
    render(<UploadZone onBrowseFiles={vi.fn()} isUploading={true} />);
    const uploadingElements = screen.getAllByText('Uploading...');
    expect(uploadingElements.length).toBeGreaterThanOrEqual(1);
  });

  it('shows upload error', () => {
    render(<UploadZone onBrowseFiles={vi.fn()} uploadError="Unsupported format" />);
    expect(screen.getByText('Unsupported format')).toBeInTheDocument();
  });

  it('includes a hidden file input for native file picker', () => {
    const { container } = render(<UploadZone onBrowseFiles={vi.fn()} />);
    const fileInput = container.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
    expect(fileInput).toHaveAttribute('accept', '.jsonl,.csv,.parquet');
    expect(fileInput).toHaveAttribute('multiple');
  });
});
