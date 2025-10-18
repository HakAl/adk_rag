import { useState, useRef, useEffect } from 'react';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
  error?: string | null;
}

export const ChatInput = ({ onSubmit, disabled, isLoading, error }: ChatInputProps) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const errorId = 'chat-input-error';

  const adjustHeight = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';

    // Set height based on content, respecting min and max
    const scrollHeight = textarea.scrollHeight;
    const minHeight = 80; // min-h-[80px]
    const maxHeight = 200; // max-h-[200px]

    const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);
    textarea.style.height = `${newHeight}px`;
  };

  useEffect(() => {
    adjustHeight();
  }, [input]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;

    onSubmit(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  return (
    <div className="flex-shrink-0">
      <form onSubmit={handleSubmit} className="flex gap-3 items-end">
        <Textarea
          ref={textareaRef}
          value={input}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder="Type your message... (Shift+Enter for new line)"
          disabled={disabled || isLoading}
          className="flex-1 min-h-[80px] max-h-[200px] resize-none transition-all focus:scale-[1.01] focus:mr-1 glass-input overflow-y-auto"
          rows={1}
          aria-label="Chat message input"
          aria-describedby={error ? errorId : undefined}
          aria-invalid={error ? 'true' : 'false'}
        />
        <Button
          type="submit"
          disabled={disabled || isLoading || !input.trim()}
          size="icon"
          className="h-10 w-10 transition-transform hover:scale-110 active:scale-95 glass-button"
          aria-label={isLoading ? 'Sending message' : 'Send message'}
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Send className="h-4 w-4" aria-hidden="true" />
          )}
        </Button>
      </form>

      {error && (
        <p
          id={errorId}
          className="text-red-400 text-sm mt-2 animate-fade-in"
          role="alert"
          aria-live="polite"
        >
          Error: {error}
        </p>
      )}
    </div>
  );
};