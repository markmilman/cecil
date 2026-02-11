import { useState, useCallback, useEffect } from 'react';
import { UploadZone } from './UploadZone';
import { QueuedFiles } from './QueuedFiles';
import { MappingConfigStep } from './MappingConfigStep';
import { ProcessingView } from './ProcessingView';
import { CompletionView } from './CompletionView';
import { apiClient } from '@/lib/apiClient';

import type { UploadedFileInfo } from '@/types';
import type { WizardStep } from '@/types';

interface WizardContainerProps {
  onBackToDashboard: () => void;
  onConfigureMapping?: (source: string) => void;
  initialMappingId?: string | null;
  onClearInitialMappingId?: () => void;
}

/**
 * WizardContainer component
 *
 * Manages the 5-step ingestion wizard flow:
 *   Step 1: UploadZone — file selection via native file picker
 *   Step 2: QueuedFiles — review uploaded files
 *   Step 3: MappingConfigStep — load or create mapping rules
 *   Step 4: ProcessingView — sanitization progress
 *   Step 5: CompletionView — results and CTA
 *
 * Owns the step state machine and the uploaded file list that
 * persists across steps. Each step transition applies a fadeIn
 * animation via the animate-fade-in CSS class.
 */
export function WizardContainer({
  onBackToDashboard,
  onConfigureMapping,
  initialMappingId,
  onClearInitialMappingId,
}: WizardContainerProps) {
  const [step, setStep] = useState<WizardStep>(1);
  const [files, setFiles] = useState<UploadedFileInfo[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [mappingId, setMappingId] = useState<string | null>(initialMappingId ?? null);
  const [outputDir, setOutputDir] = useState<string>('~/.cecil/output/');
  const [sanitizeResult, setSanitizeResult] = useState<{
    outputPath: string;
    recordsProcessed: number;
    recordsSanitized: number;
  } | null>(null);

  // When returning from the mapping editor with a mapping ID,
  // resume at step 3 with the mapping pre-loaded
  useEffect(() => {
    if (initialMappingId) {
      setMappingId(initialMappingId);
      if (files.length > 0 && step < 3) {
        setStep(3);
      }
      onClearInitialMappingId?.();
    }
  }, [initialMappingId, files.length, step, onClearInitialMappingId]);

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

  const handleMappingReady = useCallback((id: string, dir: string) => {
    setMappingId(id);
    setOutputDir(dir);
    setStep(4);
  }, []);

  const handleProcessingComplete = useCallback((result: {
    outputPath: string;
    recordsProcessed: number;
    recordsSanitized: number;
  }) => {
    setSanitizeResult(result);
    setStep(5);
  }, []);

  const handleStopProcess = useCallback(() => {
    setStep(3);
  }, []);

  const handleOpenFolder = useCallback(async () => {
    try {
      const path = sanitizeResult?.outputPath ?? outputDir;
      await apiClient.openDirectory(path);
    } catch (err) {
      // Silently fail - opening folder is a convenience feature
      console.error('Failed to open folder:', err);
    }
  }, [sanitizeResult, outputDir]);

  const handleGetReport = useCallback(() => {
    // TODO: Implement SaaS lead capture flow (US.10)
    // For now, show a placeholder message
    alert('Cost analysis reports coming soon! This feature will allow you to receive detailed cost insights and optimization recommendations.');
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
          onBack={() => setStep(1)}
        />
      )}
      {step === 3 && (
        <MappingConfigStep
          files={files}
          onReady={handleMappingReady}
          onBack={() => setStep(2)}
          onCreateMapping={(source) => onConfigureMapping?.(source)}
          initialMappingId={mappingId}
        />
      )}
      {step === 4 && (
        <ProcessingView
          source={files[0].path}
          mappingId={mappingId!}
          outputDir={outputDir}
          onComplete={handleProcessingComplete}
          onStop={handleStopProcess}
        />
      )}
      {step === 5 && (
        <CompletionView
          fileCount={files.length}
          outputPath={sanitizeResult?.outputPath ?? outputDir}
          recordsProcessed={sanitizeResult?.recordsProcessed}
          recordsSanitized={sanitizeResult?.recordsSanitized}
          onBackToDashboard={onBackToDashboard}
          onOpenFolder={handleOpenFolder}
          onGetReport={handleGetReport}
          onBack={() => setStep(3)}
        />
      )}
    </div>
  );
}
