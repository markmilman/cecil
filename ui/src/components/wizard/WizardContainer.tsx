import { useState, useCallback } from 'react';
import { UploadZone } from './UploadZone';
import { QueuedFiles } from './QueuedFiles';
import { ProcessingView } from './ProcessingView';
import { CompletionView } from './CompletionView';
import { apiClient } from '@/lib/apiClient';

import type { UploadedFileInfo } from '@/types';
import type { WizardStep } from '@/types';

interface WizardContainerProps {
  onBackToDashboard: () => void;
}

/**
 * WizardContainer component
 *
 * Manages the 4-step ingestion wizard flow:
 *   Step 1: UploadZone — file selection via native file picker
 *   Step 2: QueuedFiles — review uploaded files
 *   Step 3: ProcessingView — sanitization progress
 *   Step 4: CompletionView — results and CTA
 *
 * Owns the step state machine and the uploaded file list that
 * persists across steps. Each step transition applies a fadeIn
 * animation via the animate-fade-in CSS class.
 */
export function WizardContainer({ onBackToDashboard }: WizardContainerProps) {
  const [step, setStep] = useState<WizardStep>(1);
  const [files, setFiles] = useState<UploadedFileInfo[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleBrowseFiles = useCallback(async (fileList: FileList) => {
    setIsUploading(true);
    setUploadError(null);
    try {
      const selected = Array.from(fileList);
      const response = await apiClient.uploadFiles(selected);
      if (response.files.length > 0) {
        setFiles(response.files);
        setStep(2);
      }
      if (response.errors.length > 0) {
        setUploadError(response.errors.join('; '));
      }
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Failed to upload files');
    } finally {
      setIsUploading(false);
    }
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
        <UploadZone
          onBrowseFiles={handleBrowseFiles}
          isUploading={isUploading}
          uploadError={uploadError}
        />
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
