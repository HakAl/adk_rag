import { MessageSquarePlus, Trash2, X } from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';
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
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days} days ago`;
    return date.toLocaleDateString();
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed lg:relative inset-y-0 left-0 z-50 lg:w-1/4 w-80 transform transition-transform duration-200 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <Card className="h-full flex flex-col glass-card border-r">
          {/* Header */}
          <div className="p-4 border-b flex items-center justify-between flex-shrink-0">
            <h2 className="text-lg font-semibold gradient-text">Chat History</h2>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="lg:hidden"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* New Chat Button */}
          <div className="p-4 flex-shrink-0">
            <Button
              onClick={onNewSession}
              className="w-full flex items-center gap-2 glass-button"
            >
              <MessageSquarePlus className="h-4 w-4" />
              New Chat
            </Button>
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto p-2">
            {sessions.length === 0 ? (
              <p className="text-center text-muted-foreground text-sm py-8">
                No chat history yet
              </p>
            ) : (
              <div className="space-y-1">
                {sessions.map((session) => (
                  <div
                    key={session.sessionId}
                    className={`group relative rounded-lg p-3 cursor-pointer transition-all hover:scale-[1.02] ${
                      session.sessionId === activeSessionId
                        ? 'glass-message bg-primary/10 border border-primary/20'
                        : 'glass-message hover:bg-secondary/40'
                    }`}
                    onClick={() => onSelectSession(session.sessionId)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-sm text-foreground truncate">
                          {session.title}
                        </h3>
                        <p className="text-xs text-muted-foreground mt-1">
                          {formatDate(session.lastMessageAt)} • {session.messageCount} messages
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm('Delete this chat?')) {
                            onDeleteSession(session.sessionId);
                          }
                        }}
                      >
                        <Trash2 className="h-3 w-3 text-red-500" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>
      </div>
    </>
  );
};