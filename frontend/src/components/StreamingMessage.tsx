import { Bot } from 'lucide-react';
import { RoutingInfo } from '../api/chat';
import { Avatar } from './ChatMessage/Avatar';
import { RoutingBadge } from './ChatMessage/RoutingBadge';
import { StreamingContent } from './ChatMessage/StreamingContent';

interface StreamingMessageProps {
  content: string;
  routingInfo: RoutingInfo | null;
  isStreaming?: boolean;
}

export const StreamingMessage = ({
  content,
  routingInfo,
  isStreaming = true
}: StreamingMessageProps) => {
  return (
    <div className="flex justify-start gap-1 sm:gap-2 animate-fade-in">
      <Avatar icon={Bot} variant="bot" />

      <div className="flex-1 space-y-2">
        {routingInfo && <RoutingBadge routingInfo={routingInfo} />}

        <div
          className="glass-message bg-secondary/30 text-secondary-foreground rounded-lg px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base"
          role="status"
          aria-live="polite"
          aria-atomic="false"
        >
          <StreamingContent content={content} isStreaming={isStreaming} />
        </div>
      </div>
    </div>
  );
};