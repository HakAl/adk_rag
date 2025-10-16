import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Chat } from './Chat';
import { chatApi } from '../api/chat';

jest.mock('../api/chat');

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
    (chatApi.createSession as jest.Mock).mockResolvedValue({
      session_id: 'test-session-123',
      user_id: 'web_user',
    });
  });

  it('renders loading state initially', () => {
    render(<Chat />, { wrapper: createWrapper() });
    expect(screen.getByText('Initializing chat session...')).toBeInTheDocument();
  });

  it('renders input after session created', async () => {
    render(<Chat />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Ask a question...')).toBeInTheDocument();
      expect(screen.getByText('Send')).toBeInTheDocument();
    });
  });

  it('sends message and displays response', async () => {
    (chatApi.sendMessage as jest.Mock).mockResolvedValue({
      response: 'Test answer',
      session_id: 'test-session-123',
    });

    render(<Chat />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Ask a question...')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Ask a question...');
    const button = screen.getByText('Send');

    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText('Test question')).toBeInTheDocument();
      expect(screen.getByText('Test answer')).toBeInTheDocument();
    });
  });

  it('displays error on session creation failure', async () => {
    (chatApi.createSession as jest.Mock).mockRejectedValue(new Error('Session error'));

    render(<Chat />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/Failed to create session/)).toBeInTheDocument();
    });
  });

  it('displays error message on chat failure', async () => {
    (chatApi.sendMessage as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(<Chat />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Ask a question...')).toBeInTheDocument();
    });

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

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Ask a question...')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Ask a question...') as HTMLInputElement;
    const button = screen.getByText('Send') as HTMLButtonElement;

    fireEvent.change(input, { target: { value: 'Test' } });
    fireEvent.click(button);

    expect(input.disabled).toBe(true);
    expect(button.disabled).toBe(true);
    expect(screen.getByText('Sending...')).toBeInTheDocument();
  });
});