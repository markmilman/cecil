/**
 * Shared TypeScript type definitions for the Cecil UI
 */

/**
 * Navigation route definition
 */
export interface Route {
  path: string;
  label: string;
  icon?: string;
}

/**
 * API response wrapper
 */
export interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}
