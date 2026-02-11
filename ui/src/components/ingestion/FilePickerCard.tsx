/**
 * FilePickerCard component
 *
 * Provides a file selection card with a "Browse Files" CTA that opens the
 * browser's native file picker. Uploads selected files to the backend and
 * displays file metadata (name, size, format) after selection.
 */

import { useRef } from 'react';
import { UploadIcon, FileIcon, Trash2Icon, Loader2Icon } from 'lucide-react';
import type { UploadedFileInfo } from '@/types';

interface FilePickerCardProps {
  onFilesUploaded: (files: UploadedFileInfo[]) => void;
  uploadedFiles: UploadedFileInfo[];
  isUploading: boolean;
  uploadError: string | null;
  onBrowseClick: (files: FileList) => void;
  onRemoveFile: (index: number) => void;
  disabled?: boolean;
}

/**
 * Format file size in human-readable format
 */
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const size = bytes / Math.pow(1024, i);
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

export function FilePickerCard({
  uploadedFiles,
  isUploading,
  uploadError,
  onBrowseClick,
  onRemoveFile,
  disabled = false,
}: FilePickerCardProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onBrowseClick(files);
    }
    // Reset input so the same file can be re-selected
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Empty state — no files uploaded yet
  if (uploadedFiles.length === 0 && !isUploading) {
    return (
      <div
        className={`
          bg-white border-2 border-dashed border-slate-200 rounded-xl p-8
          transition-colors duration-200
          ${disabled ? 'opacity-50' : 'hover:border-indigo-200'}
        `}
      >
        <div className="text-center mb-6">
          <UploadIcon className="h-16 w-16 mx-auto mb-4 text-slate-300" />
          <h3 className="text-lg font-semibold text-primary mb-1">
            Select Data Files to Get Started
          </h3>
          <p className="text-sm text-muted">
            Supports JSONL, CSV, and Parquet files
          </p>
        </div>

        {/* Browse CTA */}
        <div className="flex justify-center">
          <button
            type="button"
            onClick={handleBrowseClick}
            disabled={disabled}
            className={`
              flex items-center gap-2 px-6 py-3 rounded-lg font-medium text-white
              transition-colors duration-150
              focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600
              ${disabled
                ? 'bg-slate-200 text-slate-600 cursor-not-allowed'
                : 'bg-accent hover:bg-indigo-700'
              }
            `}
          >
            <UploadIcon className="h-5 w-5" />
            Browse Files
          </button>
        </div>

        {uploadError && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-danger text-sm text-center">
            {uploadError}
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".jsonl,.csv,.parquet"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>
    );
  }

  // Uploading state
  if (isUploading) {
    return (
      <div className="bg-white border-2 border-dashed border-indigo-200 rounded-xl p-8">
        <div className="text-center">
          <Loader2Icon className="h-12 w-12 mx-auto mb-4 text-accent animate-spin" />
          <h3 className="text-lg font-semibold text-primary mb-1">
            Uploading Files...
          </h3>
          <p className="text-sm text-muted">
            Please wait while your files are being uploaded
          </p>
        </div>
      </div>
    );
  }

  // Files uploaded — show list
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-primary">
          Uploaded Files ({uploadedFiles.length})
        </h3>
        <button
          type="button"
          onClick={handleBrowseClick}
          disabled={disabled}
          className={`
            flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg
            border border-slate-200 transition-colors
            focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600
            ${disabled
              ? 'text-slate-400 cursor-not-allowed'
              : 'text-primary hover:bg-slate-50'
            }
          `}
        >
          <UploadIcon className="h-4 w-4" />
          Add More
        </button>
      </div>

      <div className="space-y-2">
        {uploadedFiles.map((file, index) => (
          <div
            key={`${file.name}-${file.path}`}
            className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg"
          >
            <FileIcon className="h-5 w-5 text-slate-400 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-primary truncate">
                {file.name}
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                {file.format && (
                  <span className="px-1.5 py-0.5 text-xs font-medium rounded bg-indigo-50 text-accent uppercase">
                    {file.format}
                  </span>
                )}
                <span className="text-xs text-muted">
                  {formatFileSize(file.size)}
                </span>
              </div>
            </div>
            <button
              type="button"
              onClick={() => onRemoveFile(index)}
              disabled={disabled}
              className={`
                flex-shrink-0 p-1.5 rounded-md transition-colors
                ${disabled
                  ? 'text-slate-300 cursor-not-allowed'
                  : 'text-slate-400 hover:text-red-500 hover:bg-red-50'
                }
              `}
              aria-label={`Remove ${file.name}`}
            >
              <Trash2Icon className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>

      {uploadError && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-danger text-sm">
          {uploadError}
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".jsonl,.csv,.parquet"
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
}
