import { Button } from '../ui/button';
import { Send, Loader2 } from 'lucide-react';

interface SubmitButtonProps {
  disabled: boolean;
  isLoading: boolean;
}

export const SubmitButton = ({ disabled, isLoading }: SubmitButtonProps) => {
  return (
    <Button
      type="submit"
      disabled={disabled}
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
  );
};