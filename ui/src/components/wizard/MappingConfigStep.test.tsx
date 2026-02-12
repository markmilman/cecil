import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MappingConfigStep } from './MappingConfigStep';
import type { UploadedFileInfo } from '@/types';

vi.mock('@/lib/apiClient', () => ({
  apiClient: {
    loadMappingYaml: vi.fn(),
  },
}));

const mockFiles: UploadedFileInfo[] = [
  { name: 'test.jsonl', path: '/tmp/test.jsonl', size: 1024, format: null },
];

describe('MappingConfigStep', () => {
  const defaultProps = {
    files: mockFiles,
    onReady: vi.fn(),
    onBack: vi.fn(),
    onCreateMapping: vi.fn(),
  };

  it('renders without crashing', () => {
    render(<MappingConfigStep {...defaultProps} />);
    expect(screen.getByText('Configure Mapping')).toBeInTheDocument();
  });

  it('shows both cards', () => {
    render(<MappingConfigStep {...defaultProps} />);
    expect(screen.getByText('Load Existing Mapping')).toBeInTheDocument();
    expect(screen.getByText('Create New Mapping')).toBeInTheDocument();
  });

  it('Start Sanitization button is disabled initially', () => {
    render(<MappingConfigStep {...defaultProps} />);
    expect(screen.getByText('Start Sanitization')).toBeDisabled();
  });

  it('calls onBack when Back is clicked', () => {
    const onBack = vi.fn();
    render(<MappingConfigStep {...defaultProps} onBack={onBack} />);
    fireEvent.click(screen.getByText('Back'));
    expect(onBack).toHaveBeenCalledOnce();
  });

  it('shows success message when initialMappingId is provided', () => {
    render(<MappingConfigStep {...defaultProps} initialMappingId="mapping-123" />);
    expect(screen.getByText('Mapping loaded from editor.')).toBeInTheDocument();
  });

  it('enables Start Sanitization when initialMappingId is provided', () => {
    render(<MappingConfigStep {...defaultProps} initialMappingId="mapping-123" />);
    expect(screen.getByText('Start Sanitization')).not.toBeDisabled();
  });
});
