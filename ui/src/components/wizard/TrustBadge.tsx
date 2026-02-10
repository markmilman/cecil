import { LockIcon } from 'lucide-react';

/**
 * TrustBadge component
 *
 * Displays a "Data stays local" pill with a lock icon.
 * Used across all wizard steps to reinforce the privacy-first message.
 */
export function TrustBadge() {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold"
      style={{
        backgroundColor: 'var(--success-bg)',
        color: 'var(--success-color)',
        border: '1px solid var(--success-color)',
        opacity: 0.8,
      }}
    >
      <LockIcon className="h-3 w-3" strokeWidth={3} />
      Data stays local
    </span>
  );
}
