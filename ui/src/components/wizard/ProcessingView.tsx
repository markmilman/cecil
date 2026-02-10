import { useState, useEffect, useRef } from 'react';
import { WizardHeader } from './WizardHeader';
import { ProgressCard } from './ProgressCard';
import { LogOutput } from './LogOutput';

const MOCK_LOG_LINES: string[] = [
  '> Processing app-logs-prod.jsonl...',
  "> Found 'api_key' pattern at line 412... [REDACTED]",
  "> Found 'email' pattern at line 890... [HASHED]",
];

/**
 * Props for the ProcessingView component
 */
interface ProcessingViewProps {
  onComplete: () => void;
  onStop: () => void;
}

/**
 * ProcessingView component (Wizard Step 3)
 *
 * Displays a progress card with animated progress bar, record count,
 * elapsed timer, and a log output area with mock redaction lines.
 * Includes a "Stop Process" danger button. When the progress bar
 * reaches 100%, auto-advances to Step 4 after a brief delay.
 *
 * The progress is simulated via setInterval and cleaned up on unmount.
 */
export function ProcessingView({ onComplete, onStop }: ProcessingViewProps) {
  const [percentComplete, setPercentComplete] = useState(0);
  const [recordCount, setRecordCount] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const completedRef = useRef(false);

  useEffect(() => {
    // Progress simulation
    intervalRef.current = setInterval(() => {
      setPercentComplete((prev) => {
        if (prev >= 100) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          if (!completedRef.current) {
            completedRef.current = true;
            setTimeout(onComplete, 500);
          }
          return 100;
        }
        return prev + 1;
      });
      setRecordCount((prev) => prev + 35);
    }, 30);

    // Elapsed time counter
    timerRef.current = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [onComplete]);

  return (
    <div>
      <WizardHeader
        title="Sanitizing Files..."
        subtitle="Please wait while we scrub PII locally."
        action={
          <button
            type="button"
            className="btn btn-danger"
            onClick={onStop}
          >
            Stop Process
          </button>
        }
      />

      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <ProgressCard
          percentComplete={percentComplete}
          recordCount={recordCount}
          elapsedSeconds={elapsedSeconds}
        />

        <LogOutput lines={MOCK_LOG_LINES} />
      </div>
    </div>
  );
}
