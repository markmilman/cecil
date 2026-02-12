/**
 * useJobList hook
 *
 * Manages state for listing job records: fetches on mount,
 * provides refresh and delete actions.
 */

import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/apiClient';

import type { JobRecord } from '@/types';

interface UseJobListState {
  jobs: JobRecord[];
  isLoading: boolean;
  error: string | null;
}

interface UseJobListReturn extends UseJobListState {
  refresh: () => Promise<void>;
  deleteJobById: (id: string) => Promise<void>;
}

export function useJobList(): UseJobListReturn {
  const [state, setState] = useState<UseJobListState>({
    jobs: [],
    isLoading: true,
    error: null,
  });

  const refresh = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const jobs = await apiClient.listJobs();
      setState({ jobs, isLoading: false, error: null });
    } catch {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'Failed to load job records',
      }));
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const deleteJobById = useCallback(async (id: string) => {
    try {
      await apiClient.deleteJob(id);
      setState((prev) => ({
        ...prev,
        jobs: prev.jobs.filter((j) => j.job_id !== id),
      }));
    } catch {
      setState((prev) => ({
        ...prev,
        error: 'Failed to delete job',
      }));
    }
  }, []);

  return {
    ...state,
    refresh,
    deleteJobById,
  };
}
