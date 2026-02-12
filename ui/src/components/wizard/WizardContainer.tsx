import { useState, useCallback, useEffect } from 'react';
import { UploadZone } from './UploadZone';
import { QueuedFiles } from './QueuedFiles';
import { MappingConfigStep } from './MappingConfigStep';
import { ProcessingView } from './ProcessingView';
import { CompletionView } from './CompletionView';
import { ResultsViewer } from './ResultsViewer';
import { apiClient } from '@/lib/apiClient';

import type { UploadedFileInfo } from '@/types';
import type { WizardStep } from '@/types';

interface WizardContainerProps {
  onBackToDashboard: () => void;
  onConfigureMapping?: (source: string) => void;
  initialMappingId?: string | null;
  onClearInitialMappingId?: () => void;
  files: UploadedFileInfo[];
  onFilesChange: (files: UploadedFileInfo[]) => void;
  step: WizardStep;
  onStepChange: (step: WizardStep) => void;
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
  files,
  onFilesChange,
  step,
  onStepChange,
}: WizardContainerProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [mappingId, setMappingId] = useState<string | null>(initialMappingId ?? null);
  const [outputDir, setOutputDir] = useState<string>('~/.cecil/output/');
  const [sanitizeResult, setSanitizeResult] = useState<{
    outputPath: string;
    recordsProcessed: number;
    recordsSanitized: number;
  } | null>(null);
  const [showResultsViewer, setShowResultsViewer] = useState(false);

  // When returning from the mapping editor with a mapping ID,
  // resume at step 3 with the mapping pre-loaded
  useEffect(() => {
    if (initialMappingId) {
      setMappingId(initialMappingId);
      if (files.length > 0) {
        onStepChange(3);
      }
      onClearInitialMappingId?.();
    }
  }, [initialMappingId, files.length, onStepChange, onClearInitialMappingId]);

  const handleBrowseFiles = useCallback(async (fileList: FileList) => {
    setIsUploading(true);
    setUploadError(null);
    try {
      const selected = Array.from(fileList);
      const response = await apiClient.uploadFiles(selected);
      if (response.files.length > 0) {
        onFilesChange(response.files);
        onStepChange(2);
      }
      if (response.errors.length > 0) {
        setUploadError(response.errors.join('; '));
      }
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Failed to upload files');
    } finally {
      setIsUploading(false);
    }
  }, [onFilesChange, onStepChange]);

  const handleRemoveFile = useCallback((index: number) => {
    onFilesChange(files.filter((_, i) => i !== index));
  }, [files, onFilesChange]);

  const handleCancel = useCallback(() => {
    onFilesChange([]);
    onStepChange(1);
  }, [onFilesChange, onStepChange]);

  const handleSanitize = useCallback(() => {
    onStepChange(3);
  }, [onStepChange]);

  const handleMappingReady = useCallback((id: string, dir: string) => {
    setMappingId(id);
    setOutputDir(dir);
    onStepChange(4);
  }, [onStepChange]);

  const handleProcessingComplete = useCallback((result: {
    outputPath: string;
    recordsProcessed: number;
    recordsSanitized: number;
  }) => {
    setSanitizeResult(result);
    onStepChange(5);
  }, [onStepChange]);

  const handleStopProcess = useCallback(() => {
    onStepChange(3);
  }, [onStepChange]);

  const handleOpenFolder = useCallback(async () => {
    try {
      const filePath = sanitizeResult?.outputPath ?? outputDir;
      // Extract parent directory — openDirectory expects a directory, not a file
      const dirPath = filePath.includes('/')
        ? filePath.substring(0, filePath.lastIndexOf('/'))
        : filePath;
      await apiClient.openDirectory(dirPath);
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

  const handleViewResults = useCallback(() => {
    setShowResultsViewer(true);
  }, []);

  const handleCloseResultsViewer = useCallback(() => {
    setShowResultsViewer(false);
  }, []);

  return (
    <>
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
          onBack={() => onStepChange(1)}
        />
      )}
      {step === 3 && (
        <MappingConfigStep
          files={files}
          onReady={handleMappingReady}
          onBack={() => onStepChange(2)}
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
          onViewResults={handleViewResults}
          onGetReport={handleGetReport}
          onBack={() => onStepChange(3)}
        />
      )}
      </div>

      {showResultsViewer && sanitizeResult?.outputPath && (
        <ResultsViewer
          outputPath={sanitizeResult.outputPath}
          onClose={handleCloseResultsViewer}
        />
      )}
    </>
  );
}
