/**
 * FileBrowserModal component
 *
 * Provides a native-like file browser experience with breadcrumb navigation,
 * keyboard controls, loading skeletons, and localStorage persistence.
 */

import { useEffect, useRef, useCallback, useMemo } from 'react';
import {
  XIcon,
  FolderIcon,
  FileIcon,
  ChevronRightIcon,
  ArrowUpIcon,
  LoaderIcon,
  AlertCircleIcon,
} from 'lucide-react';
import { useFileBrowser } from '@/hooks/useFileBrowser';
import type { FilesystemEntry } from '@/types';

export interface FileSelectionMetadata {
  name: string;
  size: number | null;
  format: string | null;
}

interface FileBrowserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (path: string, metadata: FileSelectionMetadata) => void;
  initialPath?: string;
}

/**
 * Format file size in human-readable format
 */
function formatFileSize(bytes: number | null): string {
  if (bytes === null) return '';
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const size = bytes / Math.pow(1024, i);
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

/**
 * Format a datetime string to a short date
 */
function formatDate(dateStr: string | null): string {
  if (!dateStr) return '';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return '';
  }
}

/**
 * Parse path into breadcrumb segments
 */
function parseBreadcrumbs(path: string): Array<{ label: string; path: string }> {
  const parts = path.split('/').filter(Boolean);
  const crumbs: Array<{ label: string; path: string }> = [
    { label: '/', path: '/' },
  ];

  let accumulated = '';
  for (const part of parts) {
    accumulated += '/' + part;
    crumbs.push({ label: part, path: accumulated });
  }

  return crumbs;
}

/**
 * Loading skeleton for the file list
 */
function LoadingSkeleton() {
  return (
    <div className="space-y-2 p-4" aria-label="Loading directory contents">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 py-2">
          <div className="h-5 w-5 rounded bg-slate-200 animate-pulse" />
          <div className="h-4 rounded bg-slate-200 animate-pulse" style={{ width: `${40 + (i * 8) % 40}%` }} />
        </div>
      ))}
    </div>
  );
}

export function FileBrowserModal({
  isOpen,
  onClose,
  onSelect,
  initialPath,
}: FileBrowserModalProps) {
  const {
    currentPath,
    parentPath,
    directories,
    files,
    isLoading,
    error,
    selectedFile,
    showAll,
    navigateTo,
    navigateUp,
    selectFile,
    toggleShowAll,
  } = useFileBrowser(initialPath);

  const listRef = useRef<HTMLDivElement>(null);
  const focusedIndexRef = useRef<number>(-1);
  const modalRef = useRef<HTMLDivElement>(null);

  const allItems = useMemo(() => [...directories, ...files], [directories, files]);

  const focusListItem = useCallback((index: number) => {
    if (!listRef.current) return;
    const items = listRef.current.querySelectorAll('[role="option"]');
    if (items[index]) {
      (items[index] as HTMLElement).focus();
    }
  }, []);

  // Focus trap and Escape handler
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
        return;
      }

      if (e.key === 'Backspace' && parentPath) {
        // Only if not focused on an input
        const target = e.target as HTMLElement;
        if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA') {
          e.preventDefault();
          navigateUp();
          return;
        }
      }

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        focusedIndexRef.current = Math.min(
          focusedIndexRef.current + 1,
          allItems.length - 1,
        );
        focusListItem(focusedIndexRef.current);
      }

      if (e.key === 'ArrowUp') {
        e.preventDefault();
        focusedIndexRef.current = Math.max(focusedIndexRef.current - 1, 0);
        focusListItem(focusedIndexRef.current);
      }

      if (e.key === 'Enter' && focusedIndexRef.current >= 0) {
        e.preventDefault();
        const item = allItems[focusedIndexRef.current];
        if (item) {
          if (item.is_directory) {
            navigateTo(item.path);
            focusedIndexRef.current = -1;
          } else {
            selectFile(item);
          }
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, allItems, parentPath, onClose, navigateTo, navigateUp, selectFile, focusListItem]);

  // Reset focused index when entries change
  useEffect(() => {
    focusedIndexRef.current = -1;
  }, [currentPath]);

  const handleSelect = useCallback(() => {
    if (selectedFile) {
      onSelect(selectedFile.path, {
        name: selectedFile.name,
        size: selectedFile.size,
        format: selectedFile.format,
      });
    }
  }, [selectedFile, onSelect]);

  const handleItemClick = useCallback((entry: FilesystemEntry) => {
    if (entry.is_directory) {
      navigateTo(entry.path);
    } else {
      selectFile(entry);
    }
  }, [navigateTo, selectFile]);

  if (!isOpen) return null;

  const breadcrumbs = parseBreadcrumbs(currentPath);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-label="File browser"
      ref={modalRef}
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-primary">Browse Files</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-muted hover:text-primary hover:bg-slate-100 transition-colors"
            aria-label="Close file browser"
          >
            <XIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Breadcrumb Navigation */}
        <div className="px-6 py-3 border-b border-slate-100 flex items-center gap-2 overflow-x-auto">
          {parentPath && (
            <button
              type="button"
              onClick={navigateUp}
              className="flex-shrink-0 p-1 rounded text-muted hover:text-primary hover:bg-slate-100 transition-colors"
              aria-label="Go to parent directory"
            >
              <ArrowUpIcon className="h-4 w-4" />
            </button>
          )}
          <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm min-w-0">
            {breadcrumbs.map((crumb, i) => (
              <span key={crumb.path} className="flex items-center gap-1 min-w-0">
                {i > 0 && <ChevronRightIcon className="h-3 w-3 text-slate-300 flex-shrink-0" />}
                {i === breadcrumbs.length - 1 ? (
                  <span className="font-medium text-primary truncate">{crumb.label}</span>
                ) : (
                  <button
                    type="button"
                    onClick={() => navigateTo(crumb.path)}
                    className="text-muted hover:text-accent truncate transition-colors"
                  >
                    {crumb.label}
                  </button>
                )}
              </span>
            ))}
          </nav>
        </div>

        {/* Filter Toggle */}
        <div className="px-6 py-2 border-b border-slate-100 flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-muted cursor-pointer">
            <input
              type="checkbox"
              checked={showAll}
              onChange={toggleShowAll}
              className="rounded border-slate-300 text-accent focus:ring-accent"
            />
            Show all files
          </label>
          {!isLoading && (
            <span className="text-xs text-slate-400">
              {directories.length} folders, {files.length} files
            </span>
          )}
        </div>

        {/* File List */}
        <div
          ref={listRef}
          role="listbox"
          aria-label="Directory contents"
          className="flex-1 overflow-y-auto min-h-0"
        >
          {isLoading ? (
            <LoadingSkeleton />
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
              <AlertCircleIcon className="h-10 w-10 text-slate-300 mb-3" />
              <p className="text-sm text-muted">{error}</p>
              {parentPath && (
                <button
                  type="button"
                  onClick={navigateUp}
                  className="mt-3 text-sm text-accent hover:text-indigo-700 font-medium transition-colors"
                >
                  Go back
                </button>
              )}
            </div>
          ) : allItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
              <FolderIcon className="h-10 w-10 text-slate-300 mb-3" />
              <p className="text-sm text-muted">
                {showAll ? 'This directory is empty' : 'No supported files found'}
              </p>
              {!showAll && (
                <button
                  type="button"
                  onClick={toggleShowAll}
                  className="mt-2 text-sm text-accent hover:text-indigo-700 font-medium transition-colors"
                >
                  Show all files
                </button>
              )}
            </div>
          ) : (
            <div className="py-1">
              {allItems.map((entry, index) => {
                const isSelected = selectedFile?.path === entry.path;
                const isDir = entry.is_directory;

                return (
                  <button
                    key={entry.path}
                    type="button"
                    role="option"
                    aria-selected={isSelected}
                    onClick={() => handleItemClick(entry)}
                    onFocus={() => { focusedIndexRef.current = index; }}
                    className={`
                      w-full flex items-center gap-3 px-6 py-2.5 text-left
                      transition-colors duration-100 outline-none
                      focus:bg-slate-50
                      ${isSelected
                        ? 'bg-indigo-50 border-l-4 border-accent'
                        : 'border-l-4 border-transparent hover:bg-slate-50'
                      }
                      ${!entry.is_readable && !isDir ? 'opacity-50' : ''}
                    `}
                  >
                    {isDir ? (
                      <FolderIcon className="h-5 w-5 text-amber-500 flex-shrink-0" />
                    ) : (
                      <FileIcon className="h-5 w-5 text-slate-400 flex-shrink-0" />
                    )}

                    <span className="flex-1 min-w-0">
                      <span className="text-sm font-medium text-primary truncate block">
                        {entry.name}
                      </span>
                    </span>

                    {!isDir && (
                      <span className="flex items-center gap-3 text-xs text-muted flex-shrink-0">
                        {entry.format && (
                          <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 uppercase font-medium">
                            {entry.format}
                          </span>
                        )}
                        <span>{formatFileSize(entry.size)}</span>
                        <span>{formatDate(entry.modified)}</span>
                      </span>
                    )}

                    {isDir && (
                      <ChevronRightIcon className="h-4 w-4 text-slate-300 flex-shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200 bg-slate-50 rounded-b-xl">
          <div className="text-sm text-muted truncate max-w-[60%]">
            {selectedFile ? selectedFile.path : 'No file selected'}
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-muted hover:text-primary
                border border-slate-200 rounded-lg hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSelect}
              disabled={!selectedFile}
              className={`
                px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors
                ${selectedFile
                  ? 'bg-accent hover:bg-indigo-700'
                  : 'bg-slate-300 cursor-not-allowed'
                }
              `}
            >
              Select File
            </button>
          </div>
        </div>

        {/* Loading overlay for navigation */}
        {isLoading && allItems.length > 0 && (
          <div className="absolute inset-0 bg-white/60 flex items-center justify-center rounded-xl">
            <LoaderIcon className="h-6 w-6 text-accent animate-spin" />
          </div>
        )}
      </div>
    </div>
  );
}
