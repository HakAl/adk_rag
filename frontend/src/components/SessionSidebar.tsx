import { MessageSquarePlus, X } from 'lucide-react';
import { Button } from './ui/button';
import { SlideInPanel } from './common/SlideInPanel';
import { SessionListItem } from './SessionSidebar/SessionListItem';
import { SessionMetadata } from '../hooks/useSessionStorage';

interface SessionSidebarProps {
  sessions: SessionMetadata[];
  activeSessionId: string | undefined;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionId: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

export const SessionSidebar = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  isOpen,
  onClose,
}: SessionSidebarProps) => {
  return (
    <SlideInPanel
      isOpen={isOpen}
      onClose={onClose}
      side="left"
      width="w-full sm:w-80 lg:w-1/4"
    >
      {/* Header - Mobile optimized */}
      <div className="p-3 sm:p-4 border-b flex items-center justify-between flex-shrink-0">
        <h2 className="text-base sm:text-lg font-semibold gradient-text">
          Chat History
        </h2>
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose}
          className="lg:hidden h-9 w-9 sm:h-10 sm:w-10 hover:bg-red-500/20 hover:text-red-400 transition-colors"
          aria-label="Close sidebar"
        >
          <X className="h-5 w-5 sm:h-5 sm:w-5 text-foreground" aria-hidden="true" />
        </Button>
      </div>

      {/* New Chat Button - Mobile optimized */}
      <div className="p-3 sm:p-4 flex-shrink-0">
        <Button
          onClick={onNewSession}
          className="w-full flex items-center justify-center gap-2 glass-button h-11 sm:h-10 text-sm sm:text-base"
          aria-label="Start new chat conversation"
        >
          <MessageSquarePlus className="h-4 w-4" aria-hidden="true" />
          New Chat
        </Button>
      </div>

      {/* Sessions List - Mobile optimized */}
      <nav className="flex-1 overflow-y-auto p-2" aria-label="Chat sessions">
        {sessions.length === 0 ? (
          <p className="text-center text-muted-foreground text-sm py-8 px-3">
            No chat history yet
          </p>
        ) : (
          <ul className="space-y-1" role="list">
            {sessions.map((session) => (
              <li key={session.sessionId}>
                <SessionListItem
                  session={session}
                  isActive={session.sessionId === activeSessionId}
                  onSelect={onSelectSession}
                  onDelete={onDeleteSession}
                />
              </li>
            ))}
          </ul>
        )}
      </nav>
    </SlideInPanel>
  );
};