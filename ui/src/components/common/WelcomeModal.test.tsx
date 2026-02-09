import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { WelcomeModal } from './WelcomeModal';

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

describe('WelcomeModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
  });

  it('renders when user has not been onboarded', () => {
    render(<WelcomeModal />);
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Welcome to Cecil')).toBeInTheDocument();
  });

  it('does not render when user has been onboarded', () => {
    localStorageMock.setItem('cecil:onboarded', 'true');
    render(<WelcomeModal />);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('displays the three feature items', () => {
    render(<WelcomeModal />);
    expect(screen.getByText('100% Local Processing')).toBeInTheDocument();
    expect(screen.getByText('Multiple Formats')).toBeInTheDocument();
    expect(screen.getByText('Real-Time Audit Trail')).toBeInTheDocument();
  });

  it('closes when Get Started is clicked', () => {
    const onDismiss = vi.fn();
    render(<WelcomeModal onDismiss={onDismiss} />);
    fireEvent.click(screen.getByText('Get Started'));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(onDismiss).toHaveBeenCalledOnce();
  });

  it('persists onboarded state when checkbox is checked', () => {
    render(<WelcomeModal />);
    const checkbox = screen.getByLabelText("Don't show this again");
    fireEvent.click(checkbox);
    fireEvent.click(screen.getByText('Get Started'));
    expect(localStorageMock.setItem).toHaveBeenCalledWith('cecil:onboarded', 'true');
  });

  it('does not persist when checkbox is unchecked', () => {
    render(<WelcomeModal />);
    fireEvent.click(screen.getByText('Get Started'));
    // setItem should only have been called in beforeEach clear, not for onboarded
    expect(localStorageMock.setItem).not.toHaveBeenCalledWith('cecil:onboarded', 'true');
  });

  it('has correct ARIA attributes on dialog', () => {
    render(<WelcomeModal />);
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-label', 'Welcome to Cecil');
  });
});
