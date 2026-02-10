import { useState, useCallback } from 'react';
import { ThemeProvider } from '@/components/common/ThemeProvider';
import { Shell } from '@/components/common/Shell';
import { DashboardPage } from '@/pages/DashboardPage';

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
            <DashboardPage onStartWizard={handleStartWizard} />
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
