import { useState } from 'react';
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

  return (
    <div className="flex-shrink-0">
      <form onSubmit={handleSubmit} className="flex gap-3 items-end">
        <Textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message... (Shift+Enter for new line)"
          disabled={disabled || isLoading}
          className="flex-1 min-h-[80px] max-h-[200px] resize-y transition-all focus:scale-[1.01] focus:mr-1 glass-input"
          rows={3}
        />
        <Button
          type="submit"
          disabled={disabled || isLoading}
          size="icon"
          className="h-10 w-10 transition-transform hover:scale-110 active:scale-95 glass-button"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </form>

      {error && (
        <p className="text-red-400 text-sm mt-2 animate-fade-in">Error: {error}</p>
      )}
    </div>
  );
};