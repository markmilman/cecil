/**
 * WelcomeModal component
 *
 * First-use onboarding modal shown on initial launch. Highlights Cecil's
 * key features and can be permanently dismissed. Controlled by localStorage
 * flag cecil:onboarded.
 */

import { useState, useEffect } from 'react';
import { ShieldCheckIcon, HardDriveIcon, FileTextIcon, SearchIcon } from 'lucide-react';

const STORAGE_KEY = 'cecil:onboarded';

interface WelcomeModalProps {
  onDismiss?: () => void;
}

function hasBeenOnboarded(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'true';
  } catch {
    return false;
  }
}

function setOnboarded(): void {
  try {
    localStorage.setItem(STORAGE_KEY, 'true');
  } catch {
    // Silently ignore storage errors
  }
}

const FEATURES = [
  {
    icon: <HardDriveIcon className="h-5 w-5 text-accent" />,
    title: '100% Local Processing',
    description: 'Your data never leaves your machine',
  },
  {
    icon: <FileTextIcon className="h-5 w-5 text-accent" />,
    title: 'Multiple Formats',
    description: 'Supports JSONL, CSV, and Parquet files',
  },
  {
    icon: <SearchIcon className="h-5 w-5 text-accent" />,
    title: 'Real-Time Audit Trail',
    description: 'See exactly what was sanitized',
  },
];

export function WelcomeModal({ onDismiss }: WelcomeModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [dontShowAgain, setDontShowAgain] = useState(false);

  useEffect(() => {
    if (!hasBeenOnboarded()) {
      setIsOpen(true);
    }
  }, []);

  const handleDismiss = () => {
    if (dontShowAgain) {
      setOnboarded();
    }
    setIsOpen(false);
    onDismiss?.();
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-label="Welcome to Cecil"
    >
      <div className="bg-card rounded-xl shadow-xl max-w-lg w-full mx-4 p-8">
        {/* Icon */}
        <div className="flex justify-center mb-6">
          <div className="h-16 w-16 rounded-full bg-accent-light flex items-center justify-center">
            <ShieldCheckIcon className="h-8 w-8 text-accent" />
          </div>
        </div>

        {/* Heading */}
        <h2 className="text-2xl font-bold text-center text-primary mb-6">
          Welcome to Cecil
        </h2>

        {/* Feature list */}
        <div className="space-y-4 mb-8">
          {FEATURES.map((feature) => (
            <div key={feature.title} className="flex items-start gap-3">
              <div className="flex-shrink-0 mt-0.5">{feature.icon}</div>
              <div>
                <h3 className="text-sm font-semibold text-primary">{feature.title}</h3>
                <p className="text-sm text-muted">{feature.description}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Don't show again */}
        <label className="flex items-center gap-2 text-sm text-muted mb-6 cursor-pointer">
          <input
            type="checkbox"
            checked={dontShowAgain}
            onChange={(e) => setDontShowAgain(e.target.checked)}
            className="rounded border text-accent focus:ring-accent"
            aria-label="Don't show this welcome message again"
          />
          Don&apos;t show this again
        </label>

        {/* CTA */}
        <button
          type="button"
          onClick={handleDismiss}
          className="w-full px-6 py-3 bg-accent hover:bg-accent-hover text-white rounded-lg font-medium
            transition-all duration-150 ease-out active:scale-[0.98]
            focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
        >
          Get Started
        </button>
      </div>
    </div>
  );
}
