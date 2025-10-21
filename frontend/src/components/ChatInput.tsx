import { useRef } from 'react';
import { AlertCircle } from 'lucide-react';
import { useMessageInput } from '../hooks/useMessageInput';
import { useTextareaAutoResize } from '../hooks/useTextAreaAutoResize';
import { MessageTextarea } from './ChatInput/MessageTextarea';
import { CharacterCounter } from './ChatInput/CharacterCounter';
import { SubmitButton } from './ChatInput/SubmitButton';

interface ChatInputProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
  error?: string | null;
}

export const ChatInput = ({ onSubmit, disabled, isLoading, error }: ChatInputProps) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const errorId = 'chat-input-error';

  const {
    input,
    charCount,
    validationError,
    isApproachingLimit,
    isOverLimit,
    handleChange,
    handleSubmit,
    handleKeyDown,
  } = useMessageInput({ onSubmit, disabled, isLoading });

  useTextareaAutoResize(textareaRef, input);

  // Combined error message (API error or validation error)
  const displayError = error || validationError;

  return (
    <div className="flex-shrink-0">
      <form onSubmit={handleSubmit} className="flex gap-2 sm:gap-3 items-end">
        <div className="flex-1 relative">
          <MessageTextarea
            ref={textareaRef}
            value={input}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            disabled={disabled || isLoading}
            isOverLimit={isOverLimit}
            hasError={!!displayError}
          />

          <CharacterCounter
            count={charCount}
            isApproachingLimit={isApproachingLimit}
            isOverLimit={isOverLimit}
          />
        </div>

        <SubmitButton
          disabled={disabled || isLoading || !input.trim() || isOverLimit}
          isLoading={!!isLoading}
        />
      </form>

      {/* Error display */}
      {displayError && (
        <div
          id={errorId}
          className="flex items-center gap-2 text-red-400 text-xs sm:text-sm mt-2 animate-fade-in"
          role="alert"
          aria-live="polite"
        >
          <AlertCircle className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
          <span>{displayError}</span>
        </div>
      )}

      {/* Warning for approaching limit */}
      {!displayError && isApproachingLimit && !isOverLimit && (
        <p className="text-yellow-500 text-xs sm:text-sm mt-2 animate-fade-in">
          ⚠️ Approaching character limit
        </p>
      )}
    </div>
  );
};