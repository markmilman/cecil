import { useState, useCallback } from 'react';
import { ThemeProvider } from '@/components/common/ThemeProvider';
import { Shell } from '@/components/common/Shell';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { DashboardPage } from '@/pages/DashboardPage';
import { WizardContainer } from '@/components/wizard/WizardContainer';
import { MappingPage } from '@/pages/MappingPage';
import { IngestPage } from '@/pages/IngestPage';

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
  const [mappingSource, setMappingSource] = useState<string | null>(null);
  const [wizardMappingId, setWizardMappingId] = useState<string | null>(null);

  const handleNavigate = useCallback((view: string) => {
    if (view === 'dashboard' || view === 'wizard' || view === 'mapping' || view === 'ingest') {
      setActiveView(view);
    }
  }, []);

  const handleStartWizard = useCallback(() => {
    setActiveView('wizard');
  }, []);

  const handleBackToDashboard = useCallback(() => {
    setActiveView('dashboard');
  }, []);

  const handleConfigureMapping = useCallback((source: string) => {
    setMappingSource(source);
    setActiveView('mapping');
  }, []);

  const handleMappingComplete = useCallback((mappingId: string) => {
    setWizardMappingId(mappingId);
    setActiveView('wizard');
  }, []);

  const handleClearWizardMappingId = useCallback(() => {
    setWizardMappingId(null);
  }, []);

  const handleViewResults = useCallback((source: string, scanId: string) => {
    setMappingSource(source);
    setActiveView('mapping');
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
          <ErrorBoundary key={activeView}>
            {activeView === 'dashboard' && (
              <DashboardPage onStartWizard={handleStartWizard} />
            )}
            {activeView === 'wizard' && (
              <WizardContainer
                onBackToDashboard={handleBackToDashboard}
                onConfigureMapping={handleConfigureMapping}
                initialMappingId={wizardMappingId}
                onClearInitialMappingId={handleClearWizardMappingId}
              />
            )}
            {activeView === 'mapping' && (
              <MappingPage
                source={mappingSource}
                onStartWizard={handleStartWizard}
                onBackToDashboard={handleBackToDashboard}
                onMappingComplete={handleMappingComplete}
              />
            )}
            {activeView === 'ingest' && (
              <IngestPage onViewResults={handleViewResults} />
            )}
          </ErrorBoundary>
        </div>
      </Shell>
    </ThemeProvider>
  );
}
