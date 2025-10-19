import { Trash2 } from 'lucide-react';
import { Button } from '../ui/button';
import { SessionMetadata } from '../../hooks/useSessionStorage';
import { formatSessionDate } from '../../utils/dateFormatters';

interface SessionListItemProps {
  session: SessionMetadata;
  isActive: boolean;
  onSelect: (sessionId: string) => void;
  onDelete: (sessionId: string) => void;
}

export const SessionListItem = ({
  session,
  isActive,
  onSelect,
  onDelete,
}: SessionListItemProps) => {
  const handleClick = () => {
    onSelect(session.sessionId);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(session.sessionId);
    }
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Delete this chat?')) {
      onDelete(session.sessionId);
    }
  };

  const formattedDate = formatSessionDate(session.lastMessageAt);

  return (
    <div
      className={`group relative rounded-lg p-3 cursor-pointer transition-all hover:scale-[1.02] ${
        isActive
          ? 'glass-message bg-primary/10 border border-primary/20'
          : 'glass-message hover:bg-secondary/40'
      }`}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label={`${session.title}, ${formattedDate}, ${session.messageCount} messages${
        isActive ? ', currently active' : ''
      }`}
      aria-current={isActive ? 'page' : undefined}
      onKeyDown={handleKeyDown}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-sm text-foreground truncate">
            {session.title}
          </h3>
          <p className="text-xs text-muted-foreground mt-1">
            {formattedDate} • {session.messageCount} messages
          </p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 sm:h-6 sm:w-6 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 focus:opacity-100 transition-opacity flex-shrink-0"
          onClick={handleDelete}
          aria-label={`Delete chat: ${session.title}`}
        >
          <Trash2 className="h-3 w-3 text-red-500" aria-hidden="true" />
        </Button>
      </div>
    </div>
  );
};