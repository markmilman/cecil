import { FolderIcon, FileIcon, ChevronRightIcon } from 'lucide-react';

import type { FilesystemEntry } from '@/types';

interface FileListItemProps {
  entry: FilesystemEntry;
  isSelected: boolean;
  index: number;
  onClick: (entry: FilesystemEntry) => void;
  onFocus: (index: number) => void;
}

/**
 * Format file size in human-readable format.
 */
function formatFileSize(bytes: number | null): string {
  if (bytes === null) return '';
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const size = bytes / Math.pow(1024, i);
  return `${size.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

/**
 * Format a datetime string to a short date.
 */
function formatDate(dateStr: string | null): string {
  if (!dateStr) return '';
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return '';
  }
}

/**
 * Individual file or directory entry in the file browser list.
 *
 * Renders as a button with role="option" for keyboard accessibility.
 * Directories show a folder icon and chevron; files show metadata
 * (format badge, size, modified date).
 */
export function FileListItem({
  entry,
  isSelected,
  index,
  onClick,
  onFocus,
}: FileListItemProps) {
  const isDir = entry.is_directory;

  return (
    <button
      key={entry.path}
      type="button"
      role="option"
      aria-selected={isSelected}
      onClick={() => onClick(entry)}
      onFocus={() => onFocus(index)}
      className={`
        w-full flex items-center gap-3 px-6 py-2.5 text-left
        transition-colors duration-100 outline-none
        focus:bg-subtle
        ${isSelected
          ? 'bg-accent-light border-l-4 border-accent'
          : 'border-l-4 border-transparent hover:bg-subtle'
        }
        ${!entry.is_readable && !isDir ? 'opacity-50' : ''}
      `}
    >
      {isDir ? (
        <FolderIcon className="h-5 w-5 text-amber-500 flex-shrink-0" />
      ) : (
        <FileIcon className="h-5 w-5 text-faint flex-shrink-0" />
      )}

      <span className="flex-1 min-w-0">
        <span className="text-sm font-medium text-primary truncate block">
          {entry.name}
        </span>
      </span>

      {!isDir && (
        <span className="flex items-center gap-3 text-xs text-muted flex-shrink-0">
          {entry.format && (
            <span className="px-1.5 py-0.5 rounded bg-subtle text-muted uppercase font-medium">
              {entry.format}
            </span>
          )}
          <span>{formatFileSize(entry.size)}</span>
          <span>{formatDate(entry.modified)}</span>
        </span>
      )}

      {isDir && (
        <ChevronRightIcon className="h-4 w-4 text-faint flex-shrink-0" />
      )}
    </button>
  );
}
