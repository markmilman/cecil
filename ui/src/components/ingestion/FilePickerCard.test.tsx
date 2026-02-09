import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FilePickerCard } from './FilePickerCard';

// Mock the FileBrowserModal to avoid needing API calls
vi.mock('./FileBrowserModal', () => ({
  FileBrowserModal: ({ isOpen, onClose, onSelect }: {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (path: string, meta: { name: string; size: number | null; format: string | null }) => void;
  }) => {
    if (!isOpen) return null;
    return (
      <div data-testid="file-browser-modal">
        <button onClick={onClose}>Close Modal</button>
        <button onClick={() => onSelect('/test/data.jsonl', { name: 'data.jsonl', size: 1024, format: 'jsonl' })}>
          Mock Select
        </button>
      </div>
    );
  },
}));

describe('FilePickerCard', () => {
  const mockOnFileSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('empty state', () => {
    it('renders the empty state heading', () => {
      render(<FilePickerCard onFileSelect={mockOnFileSelect} selectedFile={null} />);
      expect(screen.getByText('Select a Data File to Get Started')).toBeInTheDocument();
    });

    it('renders the Browse Files button', () => {
      render(<FilePickerCard onFileSelect={mockOnFileSelect} selectedFile={null} />);
      expect(screen.getByText('Browse Files')).toBeInTheDocument();
    });

    it('renders the manual path input', () => {
      render(<FilePickerCard onFileSelect={mockOnFileSelect} selectedFile={null} />);
      expect(screen.getByLabelText('Or enter file path manually')).toBeInTheDocument();
    });

    it('opens modal when Browse Files is clicked', () => {
      render(<FilePickerCard onFileSelect={mockOnFileSelect} selectedFile={null} />);
      fireEvent.click(screen.getByText('Browse Files'));
      expect(screen.getByTestId('file-browser-modal')).toBeInTheDocument();
    });

    it('calls onFileSelect when modal selects a file', () => {
      render(<FilePickerCard onFileSelect={mockOnFileSelect} selectedFile={null} />);
      fireEvent.click(screen.getByText('Browse Files'));
      fireEvent.click(screen.getByText('Mock Select'));
      expect(mockOnFileSelect).toHaveBeenCalledWith('/test/data.jsonl', {
        name: 'data.jsonl',
        size: 1024,
        format: 'jsonl',
      });
    });

    it('submits manual path via Use Path button', () => {
      render(<FilePickerCard onFileSelect={mockOnFileSelect} selectedFile={null} />);
      const input = screen.getByLabelText('Or enter file path manually');
      fireEvent.change(input, { target: { value: '/manual/report.csv' } });
      fireEvent.click(screen.getByText('Use Path'));
      expect(mockOnFileSelect).toHaveBeenCalledWith('/manual/report.csv', {
        name: 'report.csv',
        size: null,
        format: 'csv',
      });
    });

    it('submits manual path on Enter key', () => {
      render(<FilePickerCard onFileSelect={mockOnFileSelect} selectedFile={null} />);
      const input = screen.getByLabelText('Or enter file path manually');
      fireEvent.change(input, { target: { value: '/manual/data.jsonl' } });
      fireEvent.keyDown(input, { key: 'Enter' });
      expect(mockOnFileSelect).toHaveBeenCalledWith('/manual/data.jsonl', {
        name: 'data.jsonl',
        size: null,
        format: 'jsonl',
      });
    });

    it('disables controls when disabled prop is true', () => {
      render(<FilePickerCard onFileSelect={mockOnFileSelect} selectedFile={null} disabled />);
      expect(screen.getByText('Browse Files')).toBeDisabled();
      expect(screen.getByLabelText('Or enter file path manually')).toBeDisabled();
    });
  });

  describe('file selected state', () => {
    const selectedFile = {
      path: '/home/user/data.jsonl',
      name: 'data.jsonl',
      size: 1024,
      format: 'jsonl',
    };

    it('displays the selected file name', () => {
      render(<FilePickerCard onFileSelect={mockOnFileSelect} selectedFile={selectedFile} />);
      expect(screen.getByText('data.jsonl')).toBeInTheDocument();
    });

    it('displays the selected file path', () => {
      render(<FilePickerCard onFileSelect={mockOnFileSelect} selectedFile={selectedFile} />);
      expect(screen.getByText('/home/user/data.jsonl')).toBeInTheDocument();
    });

    it('displays the format badge', () => {
      render(<FilePickerCard onFileSelect={mockOnFileSelect} selectedFile={selectedFile} />);
      expect(screen.getByText('JSONL')).toBeInTheDocument();
    });

    it('displays the file size', () => {
      render(<FilePickerCard onFileSelect={mockOnFileSelect} selectedFile={selectedFile} />);
      expect(screen.getByText('1.0 KB')).toBeInTheDocument();
    });

    it('renders the Change File button', () => {
      render(<FilePickerCard onFileSelect={mockOnFileSelect} selectedFile={selectedFile} />);
      expect(screen.getByText('Change File')).toBeInTheDocument();
    });

    it('opens modal when Change File is clicked', async () => {
      render(<FilePickerCard onFileSelect={mockOnFileSelect} selectedFile={selectedFile} />);
      fireEvent.click(screen.getByText('Change File'));
      await waitFor(() => {
        expect(screen.getByTestId('file-browser-modal')).toBeInTheDocument();
      });
    });
  });
});
