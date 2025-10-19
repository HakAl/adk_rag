import { useState, useCallback } from 'react';
import { validateMessage, MAX_MESSAGE_LENGTH, WARNING_THRESHOLD } from '../utils/messageValidation';

interface UseMessageInputProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
}

interface UseMessageInputReturn {
  input: string;
  charCount: number;
  validationError: string | null;
  isApproachingLimit: boolean;
  isOverLimit: boolean;
  handleChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  handleSubmit: (e: React.FormEvent) => void;
  handleKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  clearInput: () => void;
}

/**
 * Hook to manage message input state and validation
 */
export const useMessageInput = ({
  onSubmit,
  disabled,
  isLoading
}: UseMessageInputProps): UseMessageInputReturn => {
  const [input, setInput] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [charCount, setCharCount] = useState(0);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    setInput(value);
    setCharCount(value.trim().length);

    // Clear validation error when user types
    if (validationError) {
      setValidationError(null);
    }
  }, [validationError]);

  const clearInput = useCallback(() => {
    setInput('');
    setCharCount(0);
    setValidationError(null);
  }, []);

  const handleSubmit = useCallback((e: React.FormEvent) => {
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
    clearInput();
  }, [input, disabled, isLoading, onSubmit, clearInput]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  }, [handleSubmit]);

  const isApproachingLimit = charCount > MAX_MESSAGE_LENGTH * WARNING_THRESHOLD;
  const isOverLimit = charCount > MAX_MESSAGE_LENGTH;

  return {
    input,
    charCount,
    validationError,
    isApproachingLimit,
    isOverLimit,
    handleChange,
    handleSubmit,
    handleKeyDown,
    clearInput
  };
};