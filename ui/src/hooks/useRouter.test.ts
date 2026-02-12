import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useRouter } from './useRouter';

describe('useRouter', () => {
  const originalPathname = window.location.pathname;

  beforeEach(() => {
    // Reset to root before each test
    window.history.replaceState({}, '', '/');
  });

  afterEach(() => {
    window.history.replaceState({}, '', originalPathname);
  });

  it('parses root path as dashboard', () => {
    window.history.replaceState({}, '', '/');
    const { result } = renderHook(() => useRouter());
    expect(result.current.view).toBe('dashboard');
    expect(result.current.params).toEqual({});
  });

  it('parses /wizard as wizard view', () => {
    window.history.replaceState({}, '', '/wizard');
    const { result } = renderHook(() => useRouter());
    expect(result.current.view).toBe('wizard');
    expect(result.current.params).toEqual({});
  });

  it('parses /mapping as mapping view without id', () => {
    window.history.replaceState({}, '', '/mapping');
    const { result } = renderHook(() => useRouter());
    expect(result.current.view).toBe('mapping');
    expect(result.current.params).toEqual({});
  });

  it('parses /mapping/:id as mapping view with mappingId', () => {
    window.history.replaceState({}, '', '/mapping/abc-123');
    const { result } = renderHook(() => useRouter());
    expect(result.current.view).toBe('mapping');
    expect(result.current.params).toEqual({ mappingId: 'abc-123' });
  });

  it('parses /ingest as ingest view', () => {
    window.history.replaceState({}, '', '/ingest');
    const { result } = renderHook(() => useRouter());
    expect(result.current.view).toBe('ingest');
    expect(result.current.params).toEqual({});
  });

  it('defaults unknown paths to dashboard', () => {
    window.history.replaceState({}, '', '/unknown/path');
    const { result } = renderHook(() => useRouter());
    expect(result.current.view).toBe('dashboard');
    expect(result.current.params).toEqual({});
  });

  it('navigate() updates view and pushes history', () => {
    const pushStateSpy = vi.spyOn(window.history, 'pushState');
    const { result } = renderHook(() => useRouter());

    act(() => {
      result.current.navigate('/wizard');
    });

    expect(result.current.view).toBe('wizard');
    expect(pushStateSpy).toHaveBeenCalledWith({}, '', '/wizard');
    pushStateSpy.mockRestore();
  });

  it('replace() updates view and replaces history', () => {
    const replaceStateSpy = vi.spyOn(window.history, 'replaceState');
    const { result } = renderHook(() => useRouter());

    act(() => {
      result.current.replace('/ingest');
    });

    expect(result.current.view).toBe('ingest');
    expect(replaceStateSpy).toHaveBeenCalledWith({}, '', '/ingest');
    replaceStateSpy.mockRestore();
  });

  it('responds to popstate events', () => {
    const { result } = renderHook(() => useRouter());
    expect(result.current.view).toBe('dashboard');

    act(() => {
      window.history.pushState({}, '', '/mapping/test-id');
      window.dispatchEvent(new PopStateEvent('popstate'));
    });

    expect(result.current.view).toBe('mapping');
    expect(result.current.params).toEqual({ mappingId: 'test-id' });
  });

  it('navigate() to /mapping/:id sets mappingId param', () => {
    const { result } = renderHook(() => useRouter());

    act(() => {
      result.current.navigate('/mapping/my-mapping');
    });

    expect(result.current.view).toBe('mapping');
    expect(result.current.params).toEqual({ mappingId: 'my-mapping' });
  });

  it('parses /job/:id as dashboard view with jobId param', () => {
    window.history.replaceState({}, '', '/job/abc-123');
    const { result } = renderHook(() => useRouter());
    expect(result.current.view).toBe('dashboard');
    expect(result.current.params).toEqual({ jobId: 'abc-123' });
  });

  it('parses /job without id as dashboard with no jobId', () => {
    window.history.replaceState({}, '', '/job');
    const { result } = renderHook(() => useRouter());
    expect(result.current.view).toBe('dashboard');
    expect(result.current.params).toEqual({});
  });

  it('handles trailing slashes', () => {
    window.history.replaceState({}, '', '/wizard/');
    const { result } = renderHook(() => useRouter());
    expect(result.current.view).toBe('wizard');
  });
});
