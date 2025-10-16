import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useSession, useChat } from '../hooks/useChat';
import { Message } from '../api/chat';

export const Chat = () => {
  const [input, setInput] = useState('');
  const userId = 'web_user';

  const queryClient = useQueryClient();
  const { data: session, isLoading: sessionLoading, error: sessionError } = useSession(userId);
  const mutation = useChat(session?.session_id, userId);

  const messages = queryClient.getQueryData<Message[]>(['messages', session?.session_id]) || [];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !session) return;

    mutation.mutate(input);
    setInput('');
  };

  if (sessionLoading) {
    return <div className="chat-loading">Initializing chat session...</div>;
  }

  if (sessionError) {
    return <div className="error">Failed to create session: {sessionError.message}</div>;
  }

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id} className="message">
            <div className="question"><strong>Q:</strong> {msg.question}</div>
            <div className="answer"><strong>A:</strong> {msg.answer}</div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="chat-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question..."
          disabled={mutation.isPending}
          className="chat-input"
        />
        <button type="submit" disabled={mutation.isPending || !session} className="chat-button">
          {mutation.isPending ? 'Sending...' : 'Send'}
        </button>
      </form>

      {mutation.isError && (
        <div className="error">Error: {mutation.error.message}</div>
      )}
    </div>
  );
};