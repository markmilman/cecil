import { ChevronRightIcon, ArrowUpIcon } from 'lucide-react';

interface BreadcrumbSegment {
  label: string;
  path: string;
}

interface BreadcrumbNavProps {
  currentPath: string;
  parentPath: string | null;
  onNavigateTo: (path: string) => void;
  onNavigateUp: () => void;
}

/**
 * Parse a filesystem path into breadcrumb segments.
 */
function parseBreadcrumbs(path: string): BreadcrumbSegment[] {
  const parts = path.split('/').filter(Boolean);
  const crumbs: BreadcrumbSegment[] = [{ label: '/', path: '/' }];

  let accumulated = '';
  for (const part of parts) {
    accumulated += '/' + part;
    crumbs.push({ label: part, path: accumulated });
  }

  return crumbs;
}

/**
 * Breadcrumb navigation bar for the file browser modal.
 *
 * Displays the current path as clickable breadcrumb segments with an
 * optional "up" button to navigate to the parent directory.
 */
export function BreadcrumbNav({
  currentPath,
  parentPath,
  onNavigateTo,
  onNavigateUp,
}: BreadcrumbNavProps) {
  const breadcrumbs = parseBreadcrumbs(currentPath);

  return (
    <div className="px-6 py-3 border-b flex items-center gap-2 overflow-x-auto">
      {parentPath && (
        <button
          type="button"
          onClick={onNavigateUp}
          className="flex-shrink-0 p-1 rounded text-muted hover:text-primary hover:bg-subtle transition-colors"
          aria-label="Go to parent directory"
        >
          <ArrowUpIcon className="h-4 w-4" />
        </button>
      )}
      <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm min-w-0">
        {breadcrumbs.map((crumb, i) => (
          <span key={crumb.path} className="flex items-center gap-1 min-w-0">
            {i > 0 && <ChevronRightIcon className="h-3 w-3 text-faint flex-shrink-0" />}
            {i === breadcrumbs.length - 1 ? (
              <span className="font-medium text-primary truncate">{crumb.label}</span>
            ) : (
              <button
                type="button"
                onClick={() => onNavigateTo(crumb.path)}
                className="text-muted hover:text-accent truncate transition-colors"
              >
                {crumb.label}
              </button>
            )}
          </span>
        ))}
      </nav>
    </div>
  );
}
