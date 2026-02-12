/**
 * FileBrowserModal component
 *
 * Provides a native-like file browser experience with breadcrumb navigation,
 * keyboard controls, loading skeletons, and localStorage persistence.
 * Delegates rendering to BreadcrumbNav and FileListItem sub-components.
 */

import { useEffect, useRef, useCallback, useMemo } from 'react';
import {
  XIcon,
  FolderIcon,
  LoaderIcon,
  AlertCircleIcon,
} from 'lucide-react';
import { useFileBrowser } from '@/hooks/useFileBrowser';
import { BreadcrumbNav } from '@/components/ingestion/BreadcrumbNav';
import { FileListItem } from '@/components/ingestion/FileListItem';

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
 * Loading skeleton for the file list
 */
function LoadingSkeleton() {
  return (
    <div className="space-y-2 p-4" aria-label="Loading directory contents">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 py-2">
          <div className="h-5 w-5 rounded bg-skeleton animate-pulse" />
          <div className="h-4 rounded bg-skeleton animate-pulse" style={{ width: `${40 + (i * 8) % 40}%` }} />
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

  const handleItemFocus = useCallback((index: number) => {
    focusedIndexRef.current = index;
  }, []);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-label="File browser"
      ref={modalRef}
    >
      <div className="bg-card rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-primary">Browse Files</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-muted hover:text-primary hover:bg-subtle transition-colors"
            aria-label="Close file browser"
          >
            <XIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Breadcrumb Navigation */}
        <BreadcrumbNav
          currentPath={currentPath}
          parentPath={parentPath}
          onNavigateTo={navigateTo}
          onNavigateUp={navigateUp}
        />

        {/* Filter Toggle */}
        <div className="px-6 py-2 border-b flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-muted cursor-pointer">
            <input
              type="checkbox"
              checked={showAll}
              onChange={toggleShowAll}
              className="rounded border text-accent focus:ring-accent"
            />
            Show all files
          </label>
          {!isLoading && (
            <span className="text-xs text-faint">
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
              <AlertCircleIcon className="h-10 w-10 text-faint mb-3" />
              <p className="text-sm text-muted">{error}</p>
              {parentPath && (
                <button
                  type="button"
                  onClick={navigateUp}
                  className="mt-3 text-sm text-accent hover:text-accent-hover font-medium transition-colors"
                >
                  Go back
                </button>
              )}
            </div>
          ) : allItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
              <FolderIcon className="h-10 w-10 text-faint mb-3" />
              <p className="text-sm text-muted">
                {showAll ? 'This directory is empty' : 'No supported files found'}
              </p>
              {!showAll && (
                <button
                  type="button"
                  onClick={toggleShowAll}
                  className="mt-2 text-sm text-accent hover:text-accent-hover font-medium transition-colors"
                >
                  Show all files
                </button>
              )}
            </div>
          ) : (
            <div className="py-1">
              {allItems.map((entry, index) => (
                <FileListItem
                  key={entry.path}
                  entry={entry}
                  isSelected={selectedFile?.path === entry.path}
                  index={index}
                  onClick={handleItemClick}
                  onFocus={handleItemFocus}
                />
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t bg-subtle rounded-b-xl">
          <div className="text-sm text-muted truncate max-w-[60%]">
            {selectedFile ? selectedFile.path : 'No file selected'}
          </div>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-muted hover:text-primary
                border rounded-lg hover:bg-subtle transition-colors"
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
                  ? 'bg-accent hover:bg-accent-hover'
                  : 'bg-skeleton cursor-not-allowed'
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
