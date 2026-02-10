import { useState, useCallback } from 'react';
import { UploadZone } from './UploadZone';
import { QueuedFiles } from './QueuedFiles';
import { ProcessingView } from './ProcessingView';
import { CompletionView } from './CompletionView';

import type { QueuedFile } from './QueuedFiles';
import type { WizardStep } from '@/types';

/**
 * Mock files added when the user "browses" in Step 1.
 * These flow through the wizard to demonstrate the full pipeline.
 */
const MOCK_FILES: QueuedFile[] = [
  { name: 'app-logs-prod.jsonl', size: '2.4 MB' },
  { name: 'api-requests-2024.csv', size: '890 KB' },
  { name: 'user-sessions.parquet', size: '1.1 MB' },
];

interface WizardContainerProps {
  onBackToDashboard: () => void;
}

/**
 * WizardContainer component
 *
 * Manages the 4-step ingestion wizard flow:
 *   Step 1: UploadZone — file selection
 *   Step 2: QueuedFiles — review queued files
 *   Step 3: ProcessingView — sanitization progress
 *   Step 4: CompletionView — results and CTA
 *
 * Owns the step state machine and the mock file list that
 * persists across steps. Each step transition applies a fadeIn
 * animation via the animate-fade-in CSS class.
 */
export function WizardContainer({ onBackToDashboard }: WizardContainerProps) {
  const [step, setStep] = useState<WizardStep>(1);
  const [files, setFiles] = useState<QueuedFile[]>([]);

  const handleBrowseFiles = useCallback(() => {
    setFiles(MOCK_FILES);
    setStep(2);
  }, []);

  const handleRemoveFile = useCallback((index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleCancel = useCallback(() => {
    setFiles([]);
    setStep(1);
  }, []);

  const handleSanitize = useCallback(() => {
    setStep(3);
  }, []);

  const handleProcessingComplete = useCallback(() => {
    setStep(4);
  }, []);

  const handleStopProcess = useCallback(() => {
    setStep(2);
  }, []);

  return (
    <div key={step} className="animate-fade-in">
      {step === 1 && (
        <UploadZone onBrowseFiles={handleBrowseFiles} />
      )}
      {step === 2 && (
        <QueuedFiles
          files={files}
          onRemoveFile={handleRemoveFile}
          onCancel={handleCancel}
          onSanitize={handleSanitize}
        />
      )}
      {step === 3 && (
        <ProcessingView
          onComplete={handleProcessingComplete}
          onStop={handleStopProcess}
        />
      )}
      {step === 4 && (
        <CompletionView
          fileCount={files.length}
          outputPath="~/.cecil/output/"
          onBackToDashboard={onBackToDashboard}
        />
      )}
    </div>
  );
}
