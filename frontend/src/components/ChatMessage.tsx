import { useState } from 'react';
import { format } from 'date-fns';
import ReactMarkdown from 'react-markdown';
import { Button } from './ui/button';
import { User, Bot, Copy, Check } from 'lucide-react';
import { Message } from '../api/chat';
import { markdownComponents } from '../utils/markdownConfig';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage = ({ message }: ChatMessageProps) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const formatTimestamp = (timestamp: number) => {
    return format(new Date(timestamp), 'h:mm a');
  };

  const handleCopy = async (messageId: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(messageId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  return (
    <div className="space-y-2 animate-fade-in">
      {/* User Question - Mobile optimized */}
      <div className="flex justify-end gap-1 sm:gap-2">
        <div className="flex flex-col items-end gap-1 max-w-[90%] sm:max-w-[85%] md:max-w-[80%]">
          <div
            className="glass-message bg-gradient-to-br from-sky-400/90 to-cyan-500/90 text-white rounded-lg px-3 sm:px-4 py-2 w-full whitespace-pre-wrap transition-all hover:scale-[1.02] hover:shadow-lg text-sm sm:text-base"
            role="article"
            aria-label="User message"
          >
            {message.question}
          </div>
          <span className="text-xs text-muted-foreground px-1">
            <time dateTime={new Date(message.timestamp).toISOString()}>
              {formatTimestamp(message.timestamp)}
            </time>
          </span>
        </div>
        <div
          className="glass-avatar bg-gradient-to-br from-sky-400 to-cyan-500 text-white rounded-full p-1.5 sm:p-2 h-7 w-7 sm:h-8 sm:w-8 flex items-center justify-center flex-shrink-0"
          aria-hidden="true"
        >
          <User className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
        </div>
      </div>

      {/* Bot Answer - Mobile optimized */}
      <div className="flex justify-start gap-1 sm:gap-2">
        <div
          className="glass-avatar bg-gradient-to-br from-primary to-accent text-primary-foreground rounded-full p-1.5 sm:p-2 h-7 w-7 sm:h-8 sm:w-8 flex items-center justify-center flex-shrink-0"
          aria-hidden="true"
        >
          <Bot className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
        </div>
        <div className="flex flex-col items-start gap-1 max-w-[90%] sm:max-w-[85%] md:max-w-[80%]">
          <div
            className="relative group glass-message bg-secondary/40 text-secondary-foreground rounded-lg px-3 sm:px-4 py-2 w-full transition-all hover:scale-[1.02] hover:shadow-lg"
            role="article"
            aria-label="Assistant response"
          >
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-1.5 right-1.5 sm:top-2 sm:right-2 h-7 w-7 sm:h-6 sm:w-6 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity focus:opacity-100"
              onClick={() => handleCopy(message.id, message.answer)}
              aria-label={copiedId === message.id ? 'Copied to clipboard' : 'Copy message to clipboard'}
            >
              {copiedId === message.id ? (
                <Check className="h-3 w-3" aria-hidden="true" />
              ) : (
                <Copy className="h-3 w-3" aria-hidden="true" />
              )}
            </Button>
            <ReactMarkdown
              className="markdown-content text-sm sm:text-base"
              components={markdownComponents}
            >
              {message.answer}
            </ReactMarkdown>
          </div>
          <span className="text-xs text-muted-foreground px-1">
            <time dateTime={new Date(message.timestamp).toISOString()}>
              {formatTimestamp(message.timestamp)}
            </time>
          </span>
        </div>
      </div>
    </div>
  );
};