import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Shell } from './Shell';
import { ThemeProvider } from './ThemeProvider';

/**
 * Helper to render Shell within required providers
 */
function renderShell(props?: {
  activeView?: string;
  onNavigate?: (view: string) => void;
  children?: React.ReactNode;
}) {
  const {
    activeView = 'dashboard',
    onNavigate = vi.fn(),
    children = <div>Test content</div>,
  } = props ?? {};

  return render(
    <ThemeProvider>
      <Shell activeView={activeView} onNavigate={onNavigate}>
        {children}
      </Shell>
    </ThemeProvider>,
  );
}

describe('Shell', () => {
  it('renders the Cecil branding', () => {
    renderShell();
    expect(screen.getByText('Cecil')).toBeInTheDocument();
  });

  it('renders navigation links', () => {
    renderShell();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Mapping Rules')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders children content', () => {
    renderShell({ children: <div>Test child content</div> });
    expect(screen.getByText('Test child content')).toBeInTheDocument();
  });

  it('renders a skip navigation link', () => {
    renderShell();
    const skipLink = screen.getByText('Skip to main content');
    expect(skipLink).toBeInTheDocument();
    expect(skipLink).toHaveAttribute('href', '#main-content');
  });

  it('has main content landmark with id', () => {
    renderShell();
    const main = screen.getByRole('main');
    expect(main).toHaveAttribute('id', 'main-content');
  });

  it('has aria-label on navigation', () => {
    renderShell();
    const nav = screen.getByRole('navigation');
    expect(nav).toHaveAttribute('aria-label', 'Main navigation');
  });

  it('marks the active view with aria-current', () => {
    renderShell({ activeView: 'dashboard' });
    const dashboardLink = screen.getByText('Dashboard');
    expect(dashboardLink).toHaveAttribute('aria-current', 'page');

    const mappingLink = screen.getByText('Mapping Rules');
    expect(mappingLink).not.toHaveAttribute('aria-current');
  });

  it('calls onNavigate when an enabled nav link is clicked', () => {
    const onNavigate = vi.fn();
    renderShell({ onNavigate, activeView: 'wizard' });

    fireEvent.click(screen.getByText('Dashboard'));
    expect(onNavigate).toHaveBeenCalledWith('dashboard');
  });

  it('does not call onNavigate when a disabled nav link is clicked', () => {
    const onNavigate = vi.fn();
    renderShell({ onNavigate });

    fireEvent.click(screen.getByText('Settings'));
    expect(onNavigate).not.toHaveBeenCalled();
  });

  it('shows "Coming soon" tooltip on disabled nav links', () => {
    renderShell();
    const settingsLink = screen.getByText('Settings');
    expect(settingsLink).toHaveAttribute('title', 'Coming soon');
    expect(settingsLink).toHaveAttribute('aria-disabled', 'true');
  });

  it('calls onNavigate when Mapping Rules is clicked', () => {
    const onNavigate = vi.fn();
    renderShell({ onNavigate, activeView: 'dashboard' });

    fireEvent.click(screen.getByText('Mapping Rules'));
    expect(onNavigate).toHaveBeenCalledWith('mapping');
  });

  it('renders the theme toggle button', () => {
    renderShell();
    const toggleButton = screen.getByTitle('Toggle Theme');
    expect(toggleButton).toBeInTheDocument();
  });

  it('theme toggle has accessible label', () => {
    renderShell();
    const toggleButton = screen.getByTitle('Toggle Theme');
    expect(toggleButton).toHaveAttribute('aria-label');
  });
});
