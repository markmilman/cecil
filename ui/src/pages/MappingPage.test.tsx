import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MappingPage } from './MappingPage';

// Mock useMapping to avoid API calls from MappingEditor
vi.mock('@/hooks/useMapping', () => ({
  useMapping: () => ({
    sampleRecord: { email: 'test@example.com', name: 'Test User' },
    fields: { email: 'redact', name: 'mask' },
    fieldOptions: {},
    defaultAction: 'redact',
    isLoading: false,
    error: null,
    validationResult: null,
    previewResult: [],
    isSaving: false,
    savedMappingId: null,
    loadSampleRecord: vi.fn(),
    setFieldAction: vi.fn(),
    setDefaultAction: vi.fn(),
    validate: vi.fn(),
    preview: vi.fn(),
    save: vi.fn(),
    reset: vi.fn(),
    dismissValidation: vi.fn(),
    dismissPreview: vi.fn(),
  }),
}));

describe('MappingPage', () => {
  it('renders the empty state when no source is provided', () => {
    render(<MappingPage onStartWizard={vi.fn()} />);
    expect(screen.getByText('No Data Source Selected')).toBeInTheDocument();
    expect(screen.getByText('Upload Data File')).toBeInTheDocument();
  });

  it('renders the empty state when source is null', () => {
    render(<MappingPage source={null} onStartWizard={vi.fn()} />);
    expect(screen.getByText('No Data Source Selected')).toBeInTheDocument();
  });

  it('renders the MappingEditor when source is provided', () => {
    render(
      <MappingPage
        source="/tmp/uploads/test.jsonl"
        onBackToDashboard={vi.fn()}
      />,
    );
    expect(screen.getByText('Configure Mapping Rules')).toBeInTheDocument();
    expect(screen.getByText('Back to Dashboard')).toBeInTheDocument();
  });

  it('renders field data from the source in the editor', () => {
    render(
      <MappingPage
        source="/tmp/uploads/test.jsonl"
        onBackToDashboard={vi.fn()}
      />,
    );
    expect(screen.getByText('email')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
    expect(screen.getByText('name')).toBeInTheDocument();
    expect(screen.getByText('Test User')).toBeInTheDocument();
  });
});
