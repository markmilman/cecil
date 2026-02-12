/**
 * useMappingList hook
 *
 * Manages state for listing mapping configurations: fetches on mount,
 * provides refresh and delete actions.
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/apiClient';

import type { MappingConfigResponse } from '@/types';

interface UseMappingListState {
  mappings: MappingConfigResponse[];
  isLoading: boolean;
  error: string | null;
}

interface UseMappingListReturn extends UseMappingListState {
  refresh: () => Promise<void>;
  deleteMappingById: (id: string) => Promise<void>;
}

export function useMappingList(): UseMappingListReturn {
  const [state, setState] = useState<UseMappingListState>({
    mappings: [],
    isLoading: true,
    error: null,
  });

  const refresh = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const mappings = await apiClient.listMappings();
      setState({ mappings, isLoading: false, error: null });
    } catch {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'Failed to load mapping configurations',
      }));
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const deleteMappingById = useCallback(async (id: string) => {
    try {
      await apiClient.deleteMapping(id);
      setState((prev) => ({
        ...prev,
        mappings: prev.mappings.filter((m) => m.mapping_id !== id),
      }));
    } catch {
      setState((prev) => ({
        ...prev,
        error: 'Failed to delete mapping',
      }));
    }
  }, []);

  return {
    ...state,
    refresh,
    deleteMappingById,
  };
}
