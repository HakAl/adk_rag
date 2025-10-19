import { Button } from '../ui/button';
import { Copy, Check } from 'lucide-react';

interface CopyButtonProps {
  messageId: string;
  text: string;
  isCopied: boolean;
  onCopy: (id: string, text: string) => void;
}

export const CopyButton = ({ messageId, text, isCopied, onCopy }: CopyButtonProps) => {
  return (
    <Button
      variant="ghost"
      size="icon"
      className="absolute top-1.5 right-1.5 sm:top-2 sm:right-2 h-7 w-7 sm:h-6 sm:w-6 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity focus:opacity-100"
      onClick={() => onCopy(messageId, text)}
      aria-label={isCopied ? 'Copied to clipboard' : 'Copy message to clipboard'}
    >
      {isCopied ? (
        <Check className="h-3 w-3" aria-hidden="true" />
      ) : (
        <Copy className="h-3 w-3" aria-hidden="true" />
      )}
    </Button>
  );
};