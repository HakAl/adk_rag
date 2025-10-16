import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Chat } from '../src/components/Chat';
import { chatApi } from '../src/api/chat';

jest.mock('../src/api/chat');

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('Chat', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders input and submit button', () => {
    render(<Chat />, { wrapper: createWrapper() });

    expect(screen.getByPlaceholderText('Ask a question...')).toBeInTheDocument();
    expect(screen.getByText('Send')).toBeInTheDocument();
  });

  it('sends message and displays response', async () => {
    (chatApi.sendMessage as jest.Mock).mockResolvedValue({
      id: '1',
      answer: 'Test answer',
    });

    render(<Chat />, { wrapper: createWrapper() });

    const input = screen.getByPlaceholderText('Ask a question...');
    const button = screen.getByText('Send');

    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('Test question')).toBeInTheDocument();
      expect(screen.getByText('Test answer')).toBeInTheDocument();
    });
  });

  it('displays error message on failure', async () => {
    (chatApi.sendMessage as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(<Chat />, { wrapper: createWrapper() });

    const input = screen.getByPlaceholderText('Ask a question...');
    const button = screen.getByText('Send');

    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/Error: API Error/)).toBeInTheDocument();
    });
  });

  it('disables input during submission', async () => {
    (chatApi.sendMessage as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(<Chat />, { wrapper: createWrapper() });

    const input = screen.getByPlaceholderText('Ask a question...') as HTMLInputElement;
    const button = screen.getByText('Send') as HTMLButtonElement;

    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.click(button);

    expect(input.disabled).toBe(true);
    expect(button.disabled).toBe(true);
    expect(screen.getByText('Sending...')).toBeInTheDocument();
  });
});