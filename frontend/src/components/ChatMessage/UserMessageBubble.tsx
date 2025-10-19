import { User } from 'lucide-react';
import { Avatar } from './Avatar';
import { MessageTimestamp } from './MessageTimestamp';

interface UserMessageBubbleProps {
  text: string;
  timestamp: number;
}

export const UserMessageBubble = ({ text, timestamp }: UserMessageBubbleProps) => {
  return (
    <div className="flex justify-end gap-1 sm:gap-2">
      <div className="flex flex-col items-end gap-1 max-w-[90%] sm:max-w-[85%] md:max-w-[80%]">
        <div
          className="glass-message bg-gradient-to-br from-sky-400/90 to-cyan-500/90 text-white rounded-lg px-3 sm:px-4 py-2 w-full whitespace-pre-wrap transition-all hover:scale-[1.02] hover:shadow-lg text-sm sm:text-base"
          role="article"
          aria-label="User message"
        >
          {text}
        </div>
        <MessageTimestamp timestamp={timestamp} />
      </div>
      <Avatar icon={User} variant="user" />
    </div>
  );
};