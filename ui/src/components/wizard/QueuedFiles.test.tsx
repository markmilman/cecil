import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueuedFiles } from './QueuedFiles';
import { FileFormat } from '@/types';

import type { UploadedFileInfo } from '@/types';

const MOCK_FILES: UploadedFileInfo[] = [
  { name: 'test-file.jsonl', path: '/tmp/uploads/test-file.jsonl', size: 2516582, format: FileFormat.JSONL },
  { name: 'data.csv', path: '/tmp/uploads/data.csv', size: 911360, format: FileFormat.CSV },
];

describe('QueuedFiles', () => {
  it('renders the heading with file count', () => {
    render(
      <QueuedFiles
        files={MOCK_FILES}
        onRemoveFile={vi.fn()}
        onCancel={vi.fn()}
        onSanitize={vi.fn()}
      />,
    );
    expect(screen.getByText('Queued Files')).toBeInTheDocument();
    expect(screen.getByText('2 Files selected for sanitization.')).toBeInTheDocument();
  });

  it('renders singular text for one file', () => {
    render(
      <QueuedFiles
        files={[MOCK_FILES[0]]}
        onRemoveFile={vi.fn()}
        onCancel={vi.fn()}
        onSanitize={vi.fn()}
      />,
    );
    expect(screen.getByText('1 File selected for sanitization.')).toBeInTheDocument();
  });

  it('renders file names and sizes', () => {
    render(
      <QueuedFiles
        files={MOCK_FILES}
        onRemoveFile={vi.fn()}
        onCancel={vi.fn()}
        onSanitize={vi.fn()}
      />,
    );
    expect(screen.getByText('test-file.jsonl')).toBeInTheDocument();
    expect(screen.getByText('data.csv')).toBeInTheDocument();
    // Sizes are formatted from bytes
    expect(screen.getByText('2.4 MB')).toBeInTheDocument();
    expect(screen.getByText('890.0 KB')).toBeInTheDocument();
  });

  it('calls onRemoveFile with correct index when remove button is clicked', () => {
    const onRemoveFile = vi.fn();
    render(
      <QueuedFiles
        files={MOCK_FILES}
        onRemoveFile={onRemoveFile}
        onCancel={vi.fn()}
        onSanitize={vi.fn()}
      />,
    );
    const removeButtons = screen.getAllByRole('button', { name: /Remove/ });
    fireEvent.click(removeButtons[1]);
    expect(onRemoveFile).toHaveBeenCalledWith(1);
  });

  it('has accessible remove buttons with file names', () => {
    render(
      <QueuedFiles
        files={MOCK_FILES}
        onRemoveFile={vi.fn()}
        onCancel={vi.fn()}
        onSanitize={vi.fn()}
      />,
    );
    expect(screen.getByRole('button', { name: 'Remove test-file.jsonl' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Remove data.csv' })).toBeInTheDocument();
  });

  it('calls onCancel when Cancel button is clicked', () => {
    const onCancel = vi.fn();
    render(
      <QueuedFiles
        files={MOCK_FILES}
        onRemoveFile={vi.fn()}
        onCancel={onCancel}
        onSanitize={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByText('Cancel'));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it('calls onSanitize when Sanitize button is clicked', () => {
    const onSanitize = vi.fn();
    render(
      <QueuedFiles
        files={MOCK_FILES}
        onRemoveFile={vi.fn()}
        onCancel={vi.fn()}
        onSanitize={onSanitize}
      />,
    );
    fireEvent.click(screen.getByText('Sanitize 2 Files'));
    expect(onSanitize).toHaveBeenCalledOnce();
  });

  it('disables sanitize button when no files', () => {
    render(
      <QueuedFiles
        files={[]}
        onRemoveFile={vi.fn()}
        onCancel={vi.fn()}
        onSanitize={vi.fn()}
      />,
    );
    expect(screen.getByText('Sanitize 0 Files')).toBeDisabled();
  });

  it('renders trust badge', () => {
    render(
      <QueuedFiles
        files={MOCK_FILES}
        onRemoveFile={vi.fn()}
        onCancel={vi.fn()}
        onSanitize={vi.fn()}
      />,
    );
    expect(screen.getByText('Data stays local')).toBeInTheDocument();
  });
});
