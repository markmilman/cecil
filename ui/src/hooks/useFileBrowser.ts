/**
 * useFileBrowser hook
 *
 * Manages state for the file browser modal: current path, entries,
 * loading state, selected file, and navigation history.
 * Calls apiClient.browsePath() on path changes and persists the
 * last-used directory in localStorage.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { apiClient } from '@/lib/apiClient';
import type { FilesystemEntry, BrowseResponse } from '@/types';

const STORAGE_KEY = 'cecil:last_directory';

interface UseFileBrowserState {
  currentPath: string;
  parentPath: string | null;
  directories: FilesystemEntry[];
  files: FilesystemEntry[];
  isLoading: boolean;
  error: string | null;
  selectedFile: FilesystemEntry | null;
  showAll: boolean;
}

interface UseFileBrowserReturn extends UseFileBrowserState {
  navigateTo: (path: string) => void;
  navigateUp: () => void;
  selectFile: (file: FilesystemEntry) => void;
  clearSelection: () => void;
  toggleShowAll: () => void;
}

/**
 * Get the initial path from localStorage or undefined (let API default to home)
 */
function getInitialPath(initialPath?: string): string | undefined {
  if (initialPath) {
    return initialPath;
  }
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return stored;
    }
  } catch {
    // localStorage may be unavailable
  }
  return undefined;
}

/**
 * Persist the current directory to localStorage
 */
function persistPath(path: string): void {
  try {
    localStorage.setItem(STORAGE_KEY, path);
  } catch {
    // Silently ignore storage errors
  }
}

export function useFileBrowser(initialPath?: string): UseFileBrowserReturn {
  const [state, setState] = useState<UseFileBrowserState>({
    currentPath: initialPath || '',
    parentPath: null,
    directories: [],
    files: [],
    isLoading: true,
    error: null,
    selectedFile: null,
    showAll: false,
  });

  const showAllRef = useRef(state.showAll);
  showAllRef.current = state.showAll;

  const fetchDirectory = useCallback(async (path?: string, showAll?: boolean) => {
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
      selectedFile: null,
    }));

    try {
      const response: BrowseResponse = await apiClient.browsePath(
        path,
        showAll ?? showAllRef.current,
      );

      if (response.error) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: response.error,
          directories: [],
          files: [],
          currentPath: response.current_path || prev.currentPath,
          parentPath: response.parent_path,
        }));
        return;
      }

      persistPath(response.current_path);

      setState((prev) => ({
        ...prev,
        isLoading: false,
        currentPath: response.current_path,
        parentPath: response.parent_path,
        directories: response.directories,
        files: response.files,
        error: null,
      }));
    } catch {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'Failed to connect to the server',
      }));
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    const startPath = getInitialPath(initialPath);
    fetchDirectory(startPath);
  }, [initialPath, fetchDirectory]);

  const navigateTo = useCallback((path: string) => {
    fetchDirectory(path);
  }, [fetchDirectory]);

  const navigateUp = useCallback(() => {
    if (state.parentPath) {
      fetchDirectory(state.parentPath);
    }
  }, [state.parentPath, fetchDirectory]);

  const selectFile = useCallback((file: FilesystemEntry) => {
    setState((prev) => ({
      ...prev,
      selectedFile: file,
    }));
  }, []);

  const clearSelection = useCallback(() => {
    setState((prev) => ({
      ...prev,
      selectedFile: null,
    }));
  }, []);

  const toggleShowAll = useCallback(() => {
    setState((prev) => {
      const newShowAll = !prev.showAll;
      // Re-fetch with new filter
      fetchDirectory(prev.currentPath, newShowAll);
      return {
        ...prev,
        showAll: newShowAll,
      };
    });
  }, [fetchDirectory]);

  return {
    ...state,
    navigateTo,
    navigateUp,
    selectFile,
    clearSelection,
    toggleShowAll,
  };
}
