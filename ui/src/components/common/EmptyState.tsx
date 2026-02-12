/**
 * EmptyState component
 *
 * Reusable empty state display with circular icon badge, heading,
 * description, and optional CTA button. Used on pages that have
 * no data yet to guide users to the next action.
 */

import { type ReactNode } from 'react';

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}: EmptyStateProps) {
  return (
    <div className="bg-card border rounded-xl p-12 shadow-sm">
      <div className="flex flex-col items-center text-center">
        {/* Circular icon badge */}
        <div className="h-20 w-20 rounded-full bg-accent-light flex items-center justify-center mb-6">
          <div className="h-10 w-10 text-accent [&>svg]:h-full [&>svg]:w-full">
            {icon}
          </div>
        </div>

        {/* Heading */}
        <h2 className="text-xl font-semibold text-primary">{title}</h2>

        {/* Description */}
        <p className="text-muted mt-2 max-w-md leading-relaxed">{description}</p>

        {/* CTA */}
        {actionLabel && onAction && (
          <button
            type="button"
            onClick={onAction}
            className="mt-6 px-6 py-3 bg-accent hover:bg-accent-hover text-white rounded-lg font-medium
              transition-all duration-150 ease-out active:scale-[0.98]
              focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            {actionLabel}
          </button>
        )}
      </div>
    </div>
  );
}
