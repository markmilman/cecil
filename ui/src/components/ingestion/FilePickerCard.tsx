/**
 * FilePickerCard component (v2)
 *
 * Provides a file selection card with a "Browse Files" CTA that opens the
 * FileBrowserModal, and a manual text input for path entry. Shows file
 * metadata (name, size, format) after selection.
 */

import { useState } from 'react';
import { UploadIcon, CheckCircleIcon, FolderOpenIcon } from 'lucide-react';
import { FileBrowserModal } from './FileBrowserModal';
import type { FileSelectionMetadata } from './FileBrowserModal';
import type { FileFormat } from '@/types';

export interface SelectedFile {
  path: string;
  name: string;
  size: number | null;
  format: string | null;
}

interface FilePickerCardProps {
  onFileSelect: (path: string, metadata: FileSelectionMetadata) => void;
  selectedFile: SelectedFile | null;
  disabled?: boolean;
}

/**
 * Format file size in human-readable format
 */
function formatFileSize(bytes: number | null): string {
  if (bytes === null) return 'Unknown size';
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const size = bytes / Math.pow(1024, i);
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

/**
 * Get a display label for a file format
 */
function formatLabel(format: string | null): string {
  if (!format) return 'Unknown format';
  return format.toUpperCase();
}

export function FilePickerCard({
  onFileSelect,
  selectedFile,
  disabled = false,
}: FilePickerCardProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [manualPath, setManualPath] = useState('');

  const handleBrowseSelect = (path: string, metadata: FileSelectionMetadata) => {
    setIsModalOpen(false);
    onFileSelect(path, metadata);
  };

  const handleManualSubmit = () => {
    const trimmed = manualPath.trim();
    if (!trimmed) return;
    // Extract name from path
    const parts = trimmed.split('/');
    const name = parts[parts.length - 1] || trimmed;
    // Try to detect format from extension
    const ext = name.includes('.') ? name.split('.').pop()?.toLowerCase() : null;
    const formatMap: Record<string, FileFormat> = {
      jsonl: 'jsonl' as FileFormat,
      csv: 'csv' as FileFormat,
      parquet: 'parquet' as FileFormat,
    };
    const format = ext ? (formatMap[ext] ?? null) : null;
    onFileSelect(trimmed, { name, size: null, format });
    setManualPath('');
  };

  const handleManualKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleManualSubmit();
    }
  };

  // Empty state — no file selected
  if (!selectedFile) {
    return (
      <>
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
              Select a Data File to Get Started
            </h3>
            <p className="text-sm text-muted">
              Supports JSONL, CSV, and Parquet files
            </p>
          </div>

          {/* Browse CTA */}
          <div className="flex justify-center mb-6">
            <button
              type="button"
              onClick={() => setIsModalOpen(true)}
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
              <FolderOpenIcon className="h-5 w-5" />
              Browse Files
            </button>
          </div>

          {/* Manual path input */}
          <div className="border-t border-slate-100 pt-4">
            <label htmlFor="manual-path" className="block text-xs font-medium text-muted mb-2">
              Or enter file path manually
            </label>
            <div className="flex items-center gap-2">
              <input
                id="manual-path"
                type="text"
                value={manualPath}
                onChange={(e) => setManualPath(e.target.value)}
                onKeyDown={handleManualKeyDown}
                disabled={disabled}
                placeholder="/path/to/data.jsonl"
                className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-lg text-primary
                  placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-accent
                  focus:border-transparent disabled:bg-slate-50 disabled:text-muted"
              />
              <button
                type="button"
                onClick={handleManualSubmit}
                disabled={disabled || !manualPath.trim()}
                className={`
                  px-4 py-2 text-sm font-medium rounded-lg transition-colors
                  focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600
                  ${disabled || !manualPath.trim()
                    ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                    : 'bg-slate-100 text-primary hover:bg-slate-200'
                  }
                `}
              >
                Use Path
              </button>
            </div>
          </div>
        </div>

        <FileBrowserModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSelect={handleBrowseSelect}
        />
      </>
    );
  }

  // File selected state
  return (
    <>
      <div
        className={`
          bg-white border border-slate-200 rounded-xl p-6
          transition-colors duration-200
          ${disabled ? 'opacity-50' : ''}
        `}
      >
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 p-2 bg-emerald-50 rounded-lg">
            <CheckCircleIcon className="h-8 w-8 text-emerald-500" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-primary truncate">
              {selectedFile.name}
            </h3>
            <p className="text-xs text-muted truncate mt-0.5" title={selectedFile.path}>
              {selectedFile.path}
            </p>
            <div className="flex items-center gap-3 mt-2">
              {selectedFile.format && (
                <span className="px-2 py-0.5 text-xs font-medium rounded bg-indigo-50 text-accent uppercase">
                  {formatLabel(selectedFile.format)}
                </span>
              )}
              <span className="text-xs text-muted">
                {formatFileSize(selectedFile.size)}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            disabled={disabled}
            className={`
              flex-shrink-0 px-4 py-2 text-sm font-medium rounded-lg
              border border-slate-200 transition-colors
              focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600
              ${disabled
                ? 'text-slate-400 cursor-not-allowed'
                : 'text-primary hover:bg-slate-50'
              }
            `}
          >
            Change File
          </button>
        </div>
      </div>

      <FileBrowserModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSelect={handleBrowseSelect}
      />
    </>
  );
}
