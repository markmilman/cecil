import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { FileBrowserModal } from './FileBrowserModal';

// Mock the apiClient module
const mockBrowsePath = vi.fn();
vi.mock('@/lib/apiClient', () => ({
  apiClient: {
    browsePath: (...args: unknown[]) => mockBrowsePath(...args),
  },
}));

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => { store[key] = value; }),
    removeItem: vi.fn((key: string) => { delete store[key]; }),
    clear: vi.fn(() => { store = {}; }),
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

const mockBrowseResponse = {
  current_path: '/home/user',
  parent_path: '/home',
  directories: [
    {
      name: 'Documents',
      path: '/home/user/Documents',
      size: null,
      modified: '2024-01-15T10:30:00Z',
      is_directory: true,
      is_readable: true,
      format: null,
    },
    {
      name: 'projects',
      path: '/home/user/projects',
      size: null,
      modified: '2024-02-01T14:00:00Z',
      is_directory: true,
      is_readable: true,
      format: null,
    },
  ],
  files: [
    {
      name: 'data.jsonl',
      path: '/home/user/data.jsonl',
      size: 1024,
      modified: '2024-03-10T08:00:00Z',
      is_directory: false,
      is_readable: true,
      format: 'jsonl',
    },
    {
      name: 'report.csv',
      path: '/home/user/report.csv',
      size: 2048,
      modified: '2024-03-11T09:00:00Z',
      is_directory: false,
      is_readable: true,
      format: 'csv',
    },
  ],
  error: null,
};

describe('FileBrowserModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
    mockBrowsePath.mockResolvedValue(mockBrowseResponse);
  });

  it('does not render when isOpen is false', () => {
    render(
      <FileBrowserModal
        isOpen={false}
        onClose={() => {}}
        onSelect={() => {}}
      />,
    );
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('renders dialog when isOpen is true', async () => {
    render(
      <FileBrowserModal
        isOpen={true}
        onClose={() => {}}
        onSelect={() => {}}
      />,
    );
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
    expect(screen.getByText('Browse Files')).toBeInTheDocument();
  });

  it('displays directories and files after loading', async () => {
    render(
      <FileBrowserModal
        isOpen={true}
        onClose={() => {}}
        onSelect={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText('Documents')).toBeInTheDocument();
    });
    expect(screen.getByText('projects')).toBeInTheDocument();
    expect(screen.getByText('data.jsonl')).toBeInTheDocument();
    expect(screen.getByText('report.csv')).toBeInTheDocument();
  });

  it('calls onClose when Cancel button is clicked', async () => {
    const onClose = vi.fn();
    render(
      <FileBrowserModal
        isOpen={true}
        onClose={onClose}
        onSelect={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Cancel'));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('calls onClose when X button is clicked', async () => {
    const onClose = vi.fn();
    render(
      <FileBrowserModal
        isOpen={true}
        onClose={onClose}
        onSelect={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByLabelText('Close file browser')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByLabelText('Close file browser'));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('navigates into a directory when clicked', async () => {
    const docsResponse = {
      ...mockBrowseResponse,
      current_path: '/home/user/Documents',
      parent_path: '/home/user',
      directories: [],
      files: [],
    };

    mockBrowsePath
      .mockResolvedValueOnce(mockBrowseResponse)
      .mockResolvedValueOnce(docsResponse);

    render(
      <FileBrowserModal
        isOpen={true}
        onClose={() => {}}
        onSelect={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText('Documents')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Documents'));

    await waitFor(() => {
      // The browsePath should have been called with the Documents path
      expect(mockBrowsePath).toHaveBeenCalledWith(
        '/home/user/Documents',
        false,
      );
    });
  });

  it('selects a file and enables Select button', async () => {
    render(
      <FileBrowserModal
        isOpen={true}
        onClose={() => {}}
        onSelect={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText('data.jsonl')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('data.jsonl'));

    // Select File button should now be enabled
    const selectButton = screen.getByText('Select File');
    expect(selectButton).not.toBeDisabled();
  });

  it('calls onSelect with file metadata when Select File is clicked', async () => {
    const onSelect = vi.fn();
    render(
      <FileBrowserModal
        isOpen={true}
        onClose={() => {}}
        onSelect={onSelect}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText('data.jsonl')).toBeInTheDocument();
    });

    // Click the file to select it
    fireEvent.click(screen.getByText('data.jsonl'));

    // Click Select File
    fireEvent.click(screen.getByText('Select File'));

    expect(onSelect).toHaveBeenCalledWith('/home/user/data.jsonl', {
      name: 'data.jsonl',
      size: 1024,
      format: 'jsonl',
    });
  });

  it('shows error state when browse fails', async () => {
    mockBrowsePath.mockResolvedValueOnce({
      current_path: '/root/restricted',
      parent_path: '/root',
      directories: [],
      files: [],
      error: 'Permission denied',
    });

    render(
      <FileBrowserModal
        isOpen={true}
        onClose={() => {}}
        onSelect={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText('Permission denied')).toBeInTheDocument();
    });
  });

  it('shows empty state when directory has no files', async () => {
    mockBrowsePath.mockResolvedValueOnce({
      current_path: '/home/user/empty',
      parent_path: '/home/user',
      directories: [],
      files: [],
      error: null,
    });

    render(
      <FileBrowserModal
        isOpen={true}
        onClose={() => {}}
        onSelect={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText('No supported files found')).toBeInTheDocument();
    });
  });

  it('disables Select File button when no file is selected', async () => {
    render(
      <FileBrowserModal
        isOpen={true}
        onClose={() => {}}
        onSelect={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText('Select File')).toBeInTheDocument();
    });

    expect(screen.getByText('Select File')).toBeDisabled();
  });

  it('displays breadcrumb navigation', async () => {
    render(
      <FileBrowserModal
        isOpen={true}
        onClose={() => {}}
        onSelect={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText('/')).toBeInTheDocument();
    });
    expect(screen.getByText('home')).toBeInTheDocument();
    expect(screen.getByText('user')).toBeInTheDocument();
  });

  it('closes on Escape key', async () => {
    const onClose = vi.fn();
    render(
      <FileBrowserModal
        isOpen={true}
        onClose={onClose}
        onSelect={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalledOnce();
  });

  it('has correct ARIA attributes on dialog', async () => {
    render(
      <FileBrowserModal
        isOpen={true}
        onClose={() => {}}
        onSelect={() => {}}
      />,
    );

    await waitFor(() => {
      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-label', 'File browser');
    });
  });

  it('has listbox role on file list', async () => {
    render(
      <FileBrowserModal
        isOpen={true}
        onClose={() => {}}
        onSelect={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByRole('listbox')).toBeInTheDocument();
    });
  });

  it('displays file format badges', async () => {
    render(
      <FileBrowserModal
        isOpen={true}
        onClose={() => {}}
        onSelect={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText('jsonl')).toBeInTheDocument();
      expect(screen.getByText('csv')).toBeInTheDocument();
    });
  });
});
