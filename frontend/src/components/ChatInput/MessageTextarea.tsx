import { forwardRef } from 'react';
import { Textarea } from '../ui/textarea';

interface MessageTextareaProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  disabled?: boolean;
  isOverLimit: boolean;
  hasError: boolean;
}

export const MessageTextarea = forwardRef<HTMLTextAreaElement, MessageTextareaProps>(
  ({ value, onChange, onKeyDown, disabled, isOverLimit, hasError }, ref) => {
    const errorId = 'chat-input-error';

    return (
      <Textarea
        ref={ref}
        value={value}
        onChange={onChange}
        onKeyDown={onKeyDown}
        placeholder="Type your message... (Shift+Enter for new line)"
        disabled={disabled}
        className={`flex-1 min-h-[60px] sm:min-h-[80px] max-h-[150px] sm:max-h-[200px] resize-none transition-all focus:scale-[1.01] focus:mr-1 glass-input overflow-y-auto text-sm sm:text-base ${
          isOverLimit ? 'border-red-500 focus:border-red-500' : ''
        }`}
        rows={1}
        aria-label="Chat message input"
        aria-describedby={hasError ? errorId : undefined}
        aria-invalid={hasError ? 'true' : 'false'}
      />
    );
  }
);

MessageTextarea.displayName = 'MessageTextarea';