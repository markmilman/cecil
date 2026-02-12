import { useCallback, useEffect, useMemo, useState } from 'react';

import type { ActiveView } from '@/types';

/**
 * Parsed route state derived from the current URL pathname.
 */
export interface RouteParams {
  mappingId?: string;
  jobId?: string;
}

export interface RouterState {
  view: ActiveView;
  params: RouteParams;
}

/**
 * Return value of the useRouter hook.
 */
export interface UseRouterReturn {
  view: ActiveView;
  params: RouteParams;
  navigate: (path: string) => void;
  replace: (path: string) => void;
}

/**
 * URL-to-view mapping scheme:
 *   /            → dashboard
 *   /job/:id     → dashboard (with jobId param, opens detail drawer)
 *   /wizard      → wizard
 *   /mapping     → mapping
 *   /mapping/:id → mapping (with mappingId param)
 *   /ingest      → ingest
 *   unknown      → dashboard (fallback)
 */
function parsePath(pathname: string): RouterState {
  const cleaned = pathname.replace(/\/+$/, '') || '/';
  const segments = cleaned.split('/').filter(Boolean);

  if (segments.length === 0) {
    return { view: 'dashboard', params: {} };
  }

  const first = segments[0];

  if (first === 'job') {
    const jobId = segments[1];
    return {
      view: 'dashboard',
      params: jobId ? { jobId } : {},
    };
  }

  if (first === 'wizard') {
    return { view: 'wizard', params: {} };
  }

  if (first === 'mapping') {
    const mappingId = segments[1];
    return {
      view: 'mapping',
      params: mappingId ? { mappingId } : {},
    };
  }

  if (first === 'ingest') {
    return { view: 'ingest', params: {} };
  }

  // Unknown paths fall back to dashboard
  return { view: 'dashboard', params: {} };
}

/**
 * Custom hook for URL-based routing using the History API.
 *
 * Parses the current pathname into a view and optional params,
 * provides navigate/replace helpers, and listens for popstate events.
 */
export function useRouter(): UseRouterReturn {
  const [state, setState] = useState<RouterState>(() =>
    parsePath(window.location.pathname),
  );

  const navigate = useCallback((path: string) => {
    window.history.pushState({}, '', path);
    setState(parsePath(path));
  }, []);

  const replace = useCallback((path: string) => {
    window.history.replaceState({}, '', path);
    setState(parsePath(path));
  }, []);

  useEffect(() => {
    const handlePopState = () => {
      setState(parsePath(window.location.pathname));
    };
    window.addEventListener('popstate', handlePopState);
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, []);

  return useMemo(
    () => ({ view: state.view, params: state.params, navigate, replace }),
    [state.view, state.params, navigate, replace],
  );
}
