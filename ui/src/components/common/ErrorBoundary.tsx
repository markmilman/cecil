import { Component } from 'react';
import { AlertCircleIcon, RefreshCwIcon } from 'lucide-react';

import type { ReactNode, ErrorInfo } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallbackTitle?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Generic error boundary for catching render errors in view-level components.
 *
 * Displays a user-friendly error screen with a retry button that resets
 * the error state, allowing the component tree to re-render.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('[ErrorBoundary] Caught render error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center p-12 text-center">
          <AlertCircleIcon className="h-12 w-12 text-danger mb-4" />
          <h2 className="text-xl font-bold text-primary mb-2">
            {this.props.fallbackTitle ?? 'Something went wrong'}
          </h2>
          <p className="text-muted mb-6 max-w-md">
            An unexpected error occurred. Try refreshing the view.
          </p>
          <button
            type="button"
            onClick={this.handleReset}
            className="flex items-center gap-2 px-6 py-3 bg-accent hover:bg-accent-hover text-white rounded-lg font-medium transition-colors duration-150"
          >
            <RefreshCwIcon className="h-4 w-4" />
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
