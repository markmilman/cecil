/**
 * Error message utilities
 *
 * Maps error types to user-friendly messages for display.
 */

/**
 * Maps error_type from ScanProgress to user-friendly messages
 */
export function getErrorMessage(errorType: string | null): string {
  switch (errorType) {
    case 'ProviderConnectionError':
    case 'file_not_found':
      return 'The specified file could not be found or is not accessible.';
    case 'ProviderReadError':
    case 'parse_error':
      return 'The file could not be parsed in the expected format.';
    case 'memory_exceeded':
      return 'The file exceeds the maximum processing size.';
    case 'ProviderDependencyError':
      return 'A required dependency is not installed for this file format.';
    default:
      return 'An unexpected error occurred during scanning.';
  }
}
