import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ErrorMessage from './ErrorMessage';

describe('ErrorMessage', () => {
  it('renders the error message', () => {
    const errorMessage = 'Something went wrong';
    render(<ErrorMessage message={errorMessage} />);

    expect(screen.getByText('Ошибка')).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('does not render a retry button if onRetry is not provided', () => {
    render(<ErrorMessage message="test message" />);

    expect(screen.queryByRole('button', { name: /Попробовать снова/i })).not.toBeInTheDocument();
  });

  it('renders a retry button if onRetry is provided', () => {
    const onRetry = () => {};
    render(<ErrorMessage message="test message" onRetry={onRetry} />);

    expect(screen.getByRole('button', { name: /Попробовать снова/i })).toBeInTheDocument();
  });
});
