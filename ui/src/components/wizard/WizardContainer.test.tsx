import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { WizardContainer } from './WizardContainer';
import { FileFormat, WizardStep, UploadedFileInfo } from '@/types';
import { useState } from 'react';

// Mock the apiClient
vi.mock('@/lib/apiClient', () => ({
  apiClient: {
    uploadFiles: vi.fn(),
    loadMappingYaml: vi.fn(),
    sanitize: vi.fn(),
  },
}));

// Import after mock setup
import { apiClient } from '@/lib/apiClient';

const MOCK_UPLOAD_RESPONSE = {
  files: [
    { name: 'app-logs-prod.jsonl', path: '/tmp/uploads/app-logs-prod.jsonl', size: 2516582, format: FileFormat.JSONL },
    { name: 'api-requests-2024.csv', path: '/tmp/uploads/api-requests-2024.csv', size: 911360, format: FileFormat.CSV },
  ],
  errors: [],
};

// Test wrapper that manages wizard state like App.tsx does
function WizardContainerWrapper(props: { onBackToDashboard?: () => void }) {
  const [files, setFiles] = useState<UploadedFileInfo[]>([]);
  const [step, setStep] = useState<WizardStep>(1);

  return (
    <WizardContainer
      onBackToDashboard={props.onBackToDashboard || vi.fn()}
      files={files}
      onFilesChange={setFiles}
      step={step}
      onStepChange={setStep}
    />
  );
}

describe('WizardContainer', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.mocked(apiClient.uploadFiles).mockResolvedValue(MOCK_UPLOAD_RESPONSE);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('starts at step 1 with UploadZone', () => {
    render(<WizardContainerWrapper />);
    expect(screen.getByText('File Ingestion')).toBeInTheDocument();
    expect(screen.getByText('Browse Files')).toBeInTheDocument();
  });

  it('advances to step 2 after file upload', async () => {
    vi.useRealTimers();
    render(<WizardContainerWrapper />);

    // Simulate selecting files via the hidden input
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test content'], 'test.jsonl', { type: 'application/json' });
    Object.defineProperty(fileInput, 'files', { value: [file], configurable: true });
    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText('Queued Files')).toBeInTheDocument();
    });
  });

  it('shows uploaded files in step 2', async () => {
    vi.useRealTimers();
    render(<WizardContainerWrapper />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.jsonl', { type: 'application/json' });
    Object.defineProperty(fileInput, 'files', { value: [file], configurable: true });
    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText('app-logs-prod.jsonl')).toBeInTheDocument();
      expect(screen.getByText('api-requests-2024.csv')).toBeInTheDocument();
    });
  });

  it('goes back to step 1 when Cancel is clicked in step 2', async () => {
    vi.useRealTimers();
    render(<WizardContainerWrapper />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.jsonl', { type: 'application/json' });
    Object.defineProperty(fileInput, 'files', { value: [file], configurable: true });
    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Cancel'));
    expect(screen.getByText('File Ingestion')).toBeInTheDocument();
  });

  it('advances to step 3 (MappingConfigStep) when Next button is clicked', async () => {
    vi.useRealTimers();
    render(<WizardContainerWrapper />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.jsonl', { type: 'application/json' });
    Object.defineProperty(fileInput, 'files', { value: [file], configurable: true });
    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText('Next: Configure Mapping')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Next: Configure Mapping'));
    expect(screen.getByText('Configure Mapping')).toBeInTheDocument();
  });

  it('goes back to step 2 when Back is clicked in step 3', async () => {
    vi.useRealTimers();
    render(<WizardContainerWrapper />);

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['test'], 'test.jsonl', { type: 'application/json' });
    Object.defineProperty(fileInput, 'files', { value: [file], configurable: true });
    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText('Next: Configure Mapping')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Next: Configure Mapping'));
    expect(screen.getByText('Configure Mapping')).toBeInTheDocument();

    fireEvent.click(screen.getByText('Back'));
    expect(screen.getByText('Queued Files')).toBeInTheDocument();
  });
});
