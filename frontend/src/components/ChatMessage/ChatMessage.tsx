import { Message } from '../../api/backend/chat.ts';
import { useCopyToClipboard } from '../../hooks/useCopyToClipboard';
import { UserMessageBubble } from './UserMessageBubble';
import { BotMessageBubble } from './BotMessageBubble';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage = ({ message }: ChatMessageProps) => {
  const { copiedId, copyToClipboard } = useCopyToClipboard();

  return (
    <div className="space-y-2 animate-fade-in">
      <UserMessageBubble
        text={message.question}
        timestamp={message.timestamp}
      />
      <BotMessageBubble
        messageId={message.id}
        text={message.answer}
        timestamp={message.timestamp}
        isCopied={copiedId === message.id}
        onCopy={copyToClipboard}
      />
    </div>
  );
};