import { useState, useRef, useEffect } from 'react';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import { Send, Loader2, AlertCircle } from 'lucide-react';

interface ChatInputProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
  error?: string | null;
}

// Client-side validation constants (should match backend)
const MAX_MESSAGE_LENGTH = 16000;  // Increased to match backend
const MIN_MESSAGE_LENGTH = 1;

// Simple client-side prompt injection detection patterns
// Removed overly aggressive patterns to allow code examples
const SUSPICIOUS_PATTERNS = [
  /ignore\s+(previous|prior|above|all)\s+(instructions?|prompts?|commands?)/i,
  /disregard\s+(previous|prior|above|all)/i,
  /forget\s+(everything|all|previous|instructions?)/i,
  /you\s+are\s+now\s+(a|an)/i,
  /system\s*:\s*/i,
  /<\|im_start\|>/i,
  /<\|im_end\|>/i,
  /\[INST\]/i,
  /\[\/INST\]/i,
  /override\s+your\s+(instructions?|programming)/i,
];

/**
 * Check if message appears to be code/technical content
 */
const isCodeContext = (message: string): boolean => {
  const codeIndicators = [
    'function', 'class', 'const', 'let', 'var', 'def', 'public', 'private',
    'import', 'require', 'return', 'if', 'else', 'for', 'while',
    '=>', 'async', 'await', '.map(', '.filter(', '.reduce(',
    'console.log', 'print(', 'System.out', 'fmt.Print'
  ];
  return codeIndicators.some(indicator => message.includes(indicator));
};

/**
 * Validate message on client side for immediate feedback
 */
const validateMessage = (message: string): { valid: boolean; error?: string } => {
  const trimmed = message.trim();

  if (trimmed.length < MIN_MESSAGE_LENGTH) {
    return { valid: false, error: 'Message cannot be empty' };
  }

  if (trimmed.length > MAX_MESSAGE_LENGTH) {
    return {
      valid: false,
      error: `Message is too long (${trimmed.length}/${MAX_MESSAGE_LENGTH} characters)`
    };
  }

  // Check for null bytes
  if (trimmed.includes('\x00')) {
    return { valid: false, error: 'Message contains invalid characters' };
  }

  // Check for suspicious patterns - skip if code context detected
  if (!isCodeContext(trimmed)) {
    for (const pattern of SUSPICIOUS_PATTERNS) {
      if (pattern.test(trimmed)) {
        return {
          valid: false,
          error: 'Message contains suspicious content. Please rephrase your query.'
        };
      }
    }
  }

  return { valid: true };
};

export const ChatInput = ({ onSubmit, disabled, isLoading, error }: ChatInputProps) => {
  const [input, setInput] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [charCount, setCharCount] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const errorId = 'chat-input-error';

  const adjustHeight = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';

    // Set height based on content, respecting min and max
    const scrollHeight = textarea.scrollHeight;
    // Mobile: smaller min/max heights
    const isMobile = window.innerWidth < 640;
    const minHeight = isMobile ? 60 : 80;
    const maxHeight = isMobile ? 150 : 200;

    const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);
    textarea.style.height = `${newHeight}px`;
  };

  useEffect(() => {
    adjustHeight();
  }, [input]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Clear previous validation error
    setValidationError(null);

    if (!input.trim() || disabled || isLoading) return;

    // Validate input before submitting
    const validation = validateMessage(input);
    if (!validation.valid) {
      setValidationError(validation.error || 'Invalid input');
      return;
    }

    // Submit and clear
    onSubmit(input.trim());
    setInput('');
    setCharCount(0);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setInput(value);
    setCharCount(value.trim().length);

    // Clear validation error when user types
    if (validationError) {
      setValidationError(null);
    }
  };

  // Determine if we should show a warning (approaching limit)
  const isApproachingLimit = charCount > MAX_MESSAGE_LENGTH * 0.9;
  const isOverLimit = charCount > MAX_MESSAGE_LENGTH;

  // Combined error message (API error or validation error)
  const displayError = error || validationError;

  return (
    <div className="flex-shrink-0">
      <form onSubmit={handleSubmit} className="flex gap-2 sm:gap-3 items-end">
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Shift+Enter for new line)"
            disabled={disabled || isLoading}
            className={`flex-1 min-h-[60px] sm:min-h-[80px] max-h-[150px] sm:max-h-[200px] resize-none transition-all focus:scale-[1.01] focus:mr-1 glass-input overflow-y-auto text-sm sm:text-base ${
              isOverLimit ? 'border-red-500 focus:border-red-500' : ''
            }`}
            rows={1}
            aria-label="Chat message input"
            aria-describedby={displayError ? errorId : undefined}
            aria-invalid={displayError ? 'true' : 'false'}
          />

          {/* Character counter */}
          {charCount > 0 && (
            <div
              className={`absolute bottom-2 right-2 text-xs transition-colors ${
                isOverLimit
                  ? 'text-red-500 font-semibold'
                  : isApproachingLimit
                  ? 'text-yellow-500'
                  : 'text-gray-400'
              }`}
              aria-live="polite"
            >
              {charCount}/{MAX_MESSAGE_LENGTH}
            </div>
          )}
        </div>

        <Button
          type="submit"
          disabled={disabled || isLoading || !input.trim() || isOverLimit}
          size="icon"
          className="h-11 w-11 sm:h-10 sm:w-10 transition-transform hover:scale-110 active:scale-95 glass-button flex-shrink-0"
          aria-label={isLoading ? 'Sending message' : 'Send message'}
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <Send className="h-4 w-4" aria-hidden="true" />
          )}
        </Button>
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