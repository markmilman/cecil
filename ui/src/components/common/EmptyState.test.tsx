import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EmptyState } from './EmptyState';

function TestIcon() {
  return <svg data-testid="test-icon" />;
}

describe('EmptyState', () => {
  it('renders the icon, title, and description', () => {
    render(
      <EmptyState
        icon={<TestIcon />}
        title="No Data"
        description="There is nothing here yet."
      />,
    );
    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
    expect(screen.getByText('No Data')).toBeInTheDocument();
    expect(screen.getByText('There is nothing here yet.')).toBeInTheDocument();
  });

  it('renders a button CTA when onAction is provided', () => {
    const onAction = vi.fn();
    render(
      <EmptyState
        icon={<TestIcon />}
        title="No Data"
        description="Nothing here."
        actionLabel="Do Something"
        onAction={onAction}
      />,
    );
    const button = screen.getByText('Do Something');
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(onAction).toHaveBeenCalledOnce();
  });

  it('does not render CTA when no actionLabel is provided', () => {
    render(
      <EmptyState
        icon={<TestIcon />}
        title="No Data"
        description="Nothing here."
      />,
    );
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('does not render CTA when only actionLabel is provided without onAction', () => {
    render(
      <EmptyState
        icon={<TestIcon />}
        title="No Data"
        description="Nothing here."
        actionLabel="Click Me"
      />,
    );
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
