import { type ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { UploadIcon, MapIcon, FileSearchIcon } from 'lucide-react';

/**
 * Props for the Shell component
 */
interface ShellProps {
  children: ReactNode;
}

/**
 * Navigation item definition
 */
interface NavItem {
  path: string;
  label: string;
  icon: ReactNode;
}

/**
 * Shell layout component
 *
 * Provides the main layout structure with navigation sidebar and content area.
 * Uses Cecil design tokens: slate-900 for primary text/nav, indigo-600 for accents.
 */
export function Shell({ children }: ShellProps) {
  const location = useLocation();

  const navItems: NavItem[] = [
    {
      path: '/ingest',
      label: 'Ingest',
      icon: <UploadIcon className="h-5 w-5" />,
    },
    {
      path: '/mapping',
      label: 'Mapping',
      icon: <MapIcon className="h-5 w-5" />,
    },
    {
      path: '/audit',
      label: 'Audit',
      icon: <FileSearchIcon className="h-5 w-5" />,
    },
  ];

  const isActiveRoute = (path: string): boolean => {
    return location.pathname === path;
  };

  return (
    <div className="flex h-full bg-slate-50">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-white border-r border-slate-200">
        <div className="flex flex-col h-full">
          {/* Logo/Header */}
          <div className="p-6 border-b border-slate-200">
            <h1 className="text-2xl font-bold text-primary">Cecil</h1>
            <p className="text-sm text-muted mt-1">Data Sanitizer & Cost Optimizer</p>
          </div>

          {/* Navigation Links */}
          <nav className="flex-1 p-4">
            <ul className="space-y-2">
              {navItems.map((item) => {
                const isActive = isActiveRoute(item.path);
                return (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      className={`
                        flex items-center gap-3 px-4 py-3 rounded-lg
                        transition-colors duration-150
                        ${
                          isActive
                            ? 'bg-accent text-white'
                            : 'text-primary hover:bg-slate-100'
                        }
                      `}
                    >
                      {item.icon}
                      <span className="font-medium">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-slate-200">
            <p className="text-xs text-muted text-center">
              Local-First, Cloud-Optional
            </p>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
