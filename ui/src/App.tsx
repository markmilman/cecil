import { useState, useCallback } from 'react';
import { ThemeProvider } from '@/components/common/ThemeProvider';
import { Shell } from '@/components/common/Shell';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { DashboardPage } from '@/pages/DashboardPage';
import { WizardContainer } from '@/components/wizard/WizardContainer';
import { MappingPage } from '@/pages/MappingPage';
import { IngestPage } from '@/pages/IngestPage';
import { useRouter } from '@/hooks/useRouter';

import type { UploadedFileInfo, WizardStep } from '@/types';

/**
 * Main App component
 *
 * Uses URL-based routing via the History API (useRouter hook).
 * The Shell receives the active view name and an onNavigate callback.
 * Wraps the entire tree in ThemeProvider for light/dark theme support.
 */
export function App() {
  const router = useRouter();
  const [mappingSource, setMappingSource] = useState<string | null>(null);
  const [wizardMappingId, setWizardMappingId] = useState<string | null>(null);
  const [wizardFiles, setWizardFiles] = useState<UploadedFileInfo[]>([]);
  const [wizardStep, setWizardStep] = useState<WizardStep>(1);

  const activeView = router.view;

  const handleNavigate = useCallback((view: string) => {
    if (view === 'dashboard') {
      router.navigate('/');
    } else if (view === 'wizard' || view === 'mapping' || view === 'ingest') {
      router.navigate(`/${view}`);
    }
  }, [router]);

  const handleViewMapping = useCallback((mappingId: string) => {
    setMappingSource(null);
    router.navigate(`/mapping/${mappingId}`);
  }, [router]);

  const handleStartWizard = useCallback(() => {
    setWizardFiles([]);
    setWizardStep(1);
    setWizardMappingId(null);
    router.navigate('/wizard');
  }, [router]);

  const handleBackToDashboard = useCallback(() => {
    setWizardFiles([]);
    setWizardStep(1);
    setWizardMappingId(null);
    router.navigate('/');
  }, [router]);

  const handleConfigureMapping = useCallback((source: string) => {
    setMappingSource(source);
    router.navigate('/mapping');
  }, [router]);

  const handleMappingComplete = useCallback((mappingId: string) => {
    setWizardMappingId(mappingId);
    router.navigate('/wizard');
  }, [router]);

  const handleClearWizardMappingId = useCallback(() => {
    setWizardMappingId(null);
  }, []);

  const handleViewResults = useCallback((source: string, _scanId: string) => {
    setMappingSource(source);
    router.navigate('/mapping');
  }, [router]);

  const handleJobSelect = useCallback((jobId: string | null) => {
    if (jobId) {
      router.replace(`/job/${jobId}`);
    } else {
      router.replace('/');
    }
  }, [router]);

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
              <DashboardPage
                onStartWizard={handleStartWizard}
                onViewMapping={handleViewMapping}
                onJobSelect={handleJobSelect}
                initialJobId={router.params.jobId}
              />
            )}
            {activeView === 'wizard' && (
              <WizardContainer
                onBackToDashboard={handleBackToDashboard}
                onConfigureMapping={handleConfigureMapping}
                initialMappingId={wizardMappingId}
                onClearInitialMappingId={handleClearWizardMappingId}
                files={wizardFiles}
                onFilesChange={setWizardFiles}
                step={wizardStep}
                onStepChange={setWizardStep}
              />
            )}
            {activeView === 'mapping' && (
              <MappingPage
                source={mappingSource}
                onStartWizard={handleStartWizard}
                onBackToDashboard={handleBackToDashboard}
                onMappingComplete={handleMappingComplete}
                initialMappingId={router.params.mappingId}
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
