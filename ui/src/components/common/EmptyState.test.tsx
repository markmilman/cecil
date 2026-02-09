import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { EmptyState } from './EmptyState';

function TestIcon() {
  return <svg data-testid="test-icon" />;
}

describe('EmptyState', () => {
  it('renders the icon, title, and description', () => {
    render(
      <BrowserRouter>
        <EmptyState
          icon={<TestIcon />}
          title="No Data"
          description="There is nothing here yet."
        />
      </BrowserRouter>,
    );
    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
    expect(screen.getByText('No Data')).toBeInTheDocument();
    expect(screen.getByText('There is nothing here yet.')).toBeInTheDocument();
  });

  it('renders a link CTA when actionHref is provided', () => {
    render(
      <BrowserRouter>
        <EmptyState
          icon={<TestIcon />}
          title="No Data"
          description="Nothing here."
          actionLabel="Go Home"
          actionHref="/home"
        />
      </BrowserRouter>,
    );
    const link = screen.getByText('Go Home');
    expect(link).toBeInTheDocument();
    expect(link.closest('a')).toHaveAttribute('href', '/home');
  });

  it('renders a button CTA when onAction is provided', () => {
    const onAction = vi.fn();
    render(
      <BrowserRouter>
        <EmptyState
          icon={<TestIcon />}
          title="No Data"
          description="Nothing here."
          actionLabel="Do Something"
          onAction={onAction}
        />
      </BrowserRouter>,
    );
    const button = screen.getByText('Do Something');
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(onAction).toHaveBeenCalledOnce();
  });

  it('does not render CTA when no actionLabel is provided', () => {
    render(
      <BrowserRouter>
        <EmptyState
          icon={<TestIcon />}
          title="No Data"
          description="Nothing here."
        />
      </BrowserRouter>,
    );
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
