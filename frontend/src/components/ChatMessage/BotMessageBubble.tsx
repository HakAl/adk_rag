import ReactMarkdown from 'react-markdown';
import { Bot } from 'lucide-react';
import { Avatar } from './Avatar';
import { MessageTimestamp } from './MessageTimestamp';
import { CopyButton } from './CopyButton';
import { markdownComponents } from '../../utils/markdownConfig';

interface BotMessageBubbleProps {
  messageId: string;
  text: string;
  timestamp: number;
  isCopied: boolean;
  onCopy: (id: string, text: string) => void;
}

export const BotMessageBubble = ({
  messageId,
  text,
  timestamp,
  isCopied,
  onCopy,
}: BotMessageBubbleProps) => {
  return (
    <div className="flex justify-start gap-1 sm:gap-2">
      <Avatar icon={Bot} variant="bot" />
      <div className="flex flex-col items-start gap-1 max-w-[90%] sm:max-w-[85%] md:max-w-[80%]">
        <div
          className="relative group glass-message bg-secondary/40 text-secondary-foreground rounded-lg px-3 sm:px-4 py-2 w-full transition-all hover:scale-[1.02] hover:shadow-lg"
          role="article"
          aria-label="Assistant response"
        >
          <CopyButton
            messageId={messageId}
            text={text}
            isCopied={isCopied}
            onCopy={onCopy}
          />
          <ReactMarkdown
            className="markdown-content text-sm sm:text-base"
            components={markdownComponents}
            disallowedElements={['script', 'iframe', 'object', 'embed', 'style']}
            unwrapDisallowed={true}
          >
            {text}
          </ReactMarkdown>
        </div>
        <MessageTimestamp timestamp={timestamp} />
      </div>
    </div>
  );
};