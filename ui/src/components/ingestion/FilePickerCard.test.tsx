import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FilePickerCard } from './FilePickerCard';
import { FileFormat } from '@/types';
import type { UploadedFileInfo } from '@/types';

describe('FilePickerCard', () => {
  const mockOnFilesUploaded = vi.fn();
  const mockOnBrowseClick = vi.fn();
  const mockOnRemoveFile = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('empty state', () => {
    it('renders the empty state heading', () => {
      render(
        <FilePickerCard
          onFilesUploaded={mockOnFilesUploaded}
          uploadedFiles={[]}
          isUploading={false}
          uploadError={null}
          onBrowseClick={mockOnBrowseClick}
          onRemoveFile={mockOnRemoveFile}
        />
      );
      expect(screen.getByText('Select Data Files to Get Started')).toBeInTheDocument();
    });

    it('renders the Browse Files button', () => {
      render(
        <FilePickerCard
          onFilesUploaded={mockOnFilesUploaded}
          uploadedFiles={[]}
          isUploading={false}
          uploadError={null}
          onBrowseClick={mockOnBrowseClick}
          onRemoveFile={mockOnRemoveFile}
        />
      );
      expect(screen.getByText('Browse Files')).toBeInTheDocument();
    });

    it('disables Browse Files button when disabled prop is true', () => {
      render(
        <FilePickerCard
          onFilesUploaded={mockOnFilesUploaded}
          uploadedFiles={[]}
          isUploading={false}
          uploadError={null}
          onBrowseClick={mockOnBrowseClick}
          onRemoveFile={mockOnRemoveFile}
          disabled
        />
      );
      expect(screen.getByText('Browse Files')).toBeDisabled();
    });

    it('displays upload error when present', () => {
      render(
        <FilePickerCard
          onFilesUploaded={mockOnFilesUploaded}
          uploadedFiles={[]}
          isUploading={false}
          uploadError="Unsupported file format"
          onBrowseClick={mockOnBrowseClick}
          onRemoveFile={mockOnRemoveFile}
        />
      );
      expect(screen.getByText('Unsupported file format')).toBeInTheDocument();
    });
  });

  describe('uploading state', () => {
    it('shows uploading spinner', () => {
      render(
        <FilePickerCard
          onFilesUploaded={mockOnFilesUploaded}
          uploadedFiles={[]}
          isUploading={true}
          uploadError={null}
          onBrowseClick={mockOnBrowseClick}
          onRemoveFile={mockOnRemoveFile}
        />
      );
      expect(screen.getByText('Uploading Files...')).toBeInTheDocument();
    });
  });

  describe('files uploaded state', () => {
    const uploadedFiles: UploadedFileInfo[] = [
      { name: 'data.jsonl', path: '/tmp/uploads/data.jsonl', size: 1024, format: FileFormat.JSONL },
      { name: 'report.csv', path: '/tmp/uploads/report.csv', size: 2048, format: FileFormat.CSV },
    ];

    it('displays the uploaded file names', () => {
      render(
        <FilePickerCard
          onFilesUploaded={mockOnFilesUploaded}
          uploadedFiles={uploadedFiles}
          isUploading={false}
          uploadError={null}
          onBrowseClick={mockOnBrowseClick}
          onRemoveFile={mockOnRemoveFile}
        />
      );
      expect(screen.getByText('data.jsonl')).toBeInTheDocument();
      expect(screen.getByText('report.csv')).toBeInTheDocument();
    });

    it('displays the file count', () => {
      render(
        <FilePickerCard
          onFilesUploaded={mockOnFilesUploaded}
          uploadedFiles={uploadedFiles}
          isUploading={false}
          uploadError={null}
          onBrowseClick={mockOnBrowseClick}
          onRemoveFile={mockOnRemoveFile}
        />
      );
      expect(screen.getByText('Uploaded Files (2)')).toBeInTheDocument();
    });

    it('displays the file sizes', () => {
      render(
        <FilePickerCard
          onFilesUploaded={mockOnFilesUploaded}
          uploadedFiles={uploadedFiles}
          isUploading={false}
          uploadError={null}
          onBrowseClick={mockOnBrowseClick}
          onRemoveFile={mockOnRemoveFile}
        />
      );
      expect(screen.getByText('1.0 KB')).toBeInTheDocument();
      expect(screen.getByText('2.0 KB')).toBeInTheDocument();
    });

    it('displays format badges', () => {
      render(
        <FilePickerCard
          onFilesUploaded={mockOnFilesUploaded}
          uploadedFiles={uploadedFiles}
          isUploading={false}
          uploadError={null}
          onBrowseClick={mockOnBrowseClick}
          onRemoveFile={mockOnRemoveFile}
        />
      );
      expect(screen.getByText('jsonl')).toBeInTheDocument();
      expect(screen.getByText('csv')).toBeInTheDocument();
    });

    it('renders Add More button', () => {
      render(
        <FilePickerCard
          onFilesUploaded={mockOnFilesUploaded}
          uploadedFiles={uploadedFiles}
          isUploading={false}
          uploadError={null}
          onBrowseClick={mockOnBrowseClick}
          onRemoveFile={mockOnRemoveFile}
        />
      );
      expect(screen.getByText('Add More')).toBeInTheDocument();
    });

    it('calls onRemoveFile when remove button is clicked', () => {
      render(
        <FilePickerCard
          onFilesUploaded={mockOnFilesUploaded}
          uploadedFiles={uploadedFiles}
          isUploading={false}
          uploadError={null}
          onBrowseClick={mockOnBrowseClick}
          onRemoveFile={mockOnRemoveFile}
        />
      );
      fireEvent.click(screen.getByLabelText('Remove data.jsonl'));
      expect(mockOnRemoveFile).toHaveBeenCalledWith(0);
    });
  });
});
