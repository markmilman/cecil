import { useState, useCallback } from 'react';
import { ThemeProvider } from '@/components/common/ThemeProvider';
import { Shell } from '@/components/common/Shell';

import type { ActiveView } from '@/types';

/**
 * Main App component
 *
 * Uses state-driven view switching instead of React Router.
 * The Shell receives the active view name and an onNavigate callback.
 * Wraps the entire tree in ThemeProvider for light/dark theme support.
 */
export function App() {
  const [activeView, setActiveView] = useState<ActiveView>('dashboard');

  const handleNavigate = useCallback((view: string) => {
    if (view === 'dashboard' || view === 'wizard') {
      setActiveView(view);
    }
  }, []);

  const handleStartWizard = useCallback(() => {
    setActiveView('wizard');
  }, []);

  const handleBackToDashboard = useCallback(() => {
    setActiveView('dashboard');
  }, []);

  return (
    <ThemeProvider>
      <Shell activeView={activeView} onNavigate={handleNavigate}>
        <div
          className="animate-fade-in"
          style={{
            maxWidth: '1200px',
            margin: '0 auto',
            width: '100%',
            padding: '32px',
            boxSizing: 'border-box',
          }}
        >
          {activeView === 'dashboard' && (
            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '24px',
                }}
              >
                <div>
                  <h2
                    style={{
                      margin: 0,
                      fontSize: '24px',
                      color: 'var(--text-primary)',
                    }}
                  >
                    Audit Dashboard
                  </h2>
                  <p
                    style={{
                      margin: '4px 0 0',
                      color: 'var(--text-secondary)',
                      fontSize: '14px',
                    }}
                  >
                    Overview of recent sanitization jobs and PII detection.
                  </p>
                </div>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleStartWizard}
                >
                  <span style={{ fontSize: '18px' }}>+</span> New Sanitization Job
                </button>
              </div>
              {/* Stats grid and job history table will be added by subsequent sub-issues */}
            </div>
          )}
          {activeView === 'wizard' && (
            <div>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleBackToDashboard}
                style={{ marginBottom: '24px' }}
              >
                Back to Dashboard
              </button>
              {/* Wizard steps will be added by subsequent sub-issues */}
            </div>
          )}
        </div>
      </Shell>
    </ThemeProvider>
  );
}
