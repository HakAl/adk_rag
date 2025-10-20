import { useState } from 'react';
import { useChatStream } from '../hooks/useChatStream';
import { useSessionManager } from '../hooks/useSessionManager';
import { useMessageManager } from '../hooks/useMessageManager';
import { useAutoScroll } from '../hooks/useAutoScroll';
import { useMessagePersistence } from '../hooks/useMessagePersistence';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Loader2, Menu, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import { ChatMessage } from './ChatMessage/index';
import { StreamingMessage } from './StreamingMessage';
import { ChatInput } from './ChatInput';
import { SessionSidebar } from './SessionSidebar';

export const Chat = () => {
  const { user } = useAuth();
  const userId = user?.user_id || 'web_user';
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Session management
  const {
    currentSessionId,
    isInitializing,
    initError,
    sessions,
    createNewSession,
    switchSession,
    removeSession,
    retryInitialization,
    updateSessionMetadata,
  } = useSessionManager();

  // Message management
  const {
    messages,
    easterEggMessages,
    addOptimisticMessage,
    clearEasterEggs,
    handleEasterEgg,
  } = useMessageManager(currentSessionId);

  // Chat streaming
  const {
    sendMessage,
    isStreaming,
    error: streamError,
    routingInfo,
    streamingContent
  } = useChatStream(currentSessionId, userId);

  // Auto-scroll on message changes
  const scrollRef = useAutoScroll({
    dependencies: [messages.length, isStreaming, streamingContent],
  });

  // Persist messages to localStorage
  useMessagePersistence({
    sessionId: currentSessionId,
    messages,
    updateSessionMetadata,
  });

  // Handle new session creation
  const handleNewSession = async () => {
    try {
      await createNewSession();
      clearEasterEggs();
      setSidebarOpen(false);
    } catch (error) {
      console.error('Failed to create new session:', error);
    }
  };

  // Handle session selection
  const handleSelectSession = (sessionId: string) => {
    switchSession(sessionId);
    clearEasterEggs();
    setSidebarOpen(false);
  };

  // Handle session deletion
  const handleDeleteSession = (sessionId: string) => {
    removeSession(sessionId);
  };

  // Handle message submission
  const handleSubmit = async (input: string) => {
    if (!currentSessionId) return;

    // Check for easter eggs first
    if (handleEasterEgg(input)) {
      return;
    }

    // Clear easter eggs when asking a real question
    clearEasterEggs();

    // Add optimistic message immediately
    addOptimisticMessage(input);

    // Send message with streaming
    await sendMessage(input);
  };

  // Show initialization error with retry option
  if (initError) {
    return (
      <div className="flex h-screen items-center justify-center p-4">
        <Card className="glass-card border-red-500/50 max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-500">
              <AlertCircle className="h-5 w-5" />
              Initialization Failed
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Failed to initialize chat session. Please try again.
            </p>
            <p className="text-xs text-red-400">
              Error: {initError.message}
            </p>
            <Button
              onClick={retryInitialization}
              className="w-full"
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show loading state during initialization
  if (isInitializing) {
    return (
      <div className="flex h-screen items-center justify-center p-4">
        <Card className="glass-card">
          <CardContent className="p-4 sm:p-6">
            <div className="flex items-center justify-center gap-2" role="status" aria-live="polite">
              <Loader2 className="h-4 w-4 animate-spin text-primary" aria-hidden="true" />
              <p className="text-foreground text-sm sm:text-base">Initializing chat session...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex gap-2 sm:gap-4 h-full">
      <SessionSidebar
        sessions={sessions}
        activeSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="flex-1 flex flex-col min-w-0 h-full" id="main-content">
        <Card className="h-full flex flex-col glass-card gradient-border">
          <CardHeader className="flex-shrink-0 flex flex-row items-center gap-2 sm:gap-3 p-3 sm:p-6">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden h-9 w-9 sm:h-10 sm:w-10"
              aria-label="Open chat history sidebar"
              aria-expanded={sidebarOpen}
              aria-controls="chat-sidebar"
            >
              <Menu className="h-4 w-4 sm:h-5 sm:w-5" aria-hidden="true" />
            </Button>
            <CardTitle className="gradient-text text-lg sm:text-xl md:text-2xl">Chat</CardTitle>
          </CardHeader>

          <CardContent className="flex-1 flex flex-col min-h-0 p-3 sm:pb-4 sm:px-6">
            <ScrollArea
              ref={scrollRef}
              className="flex-1 mb-3 sm:mb-4 pr-2 sm:pr-4"
              role="log"
              aria-live="polite"
              aria-atomic="false"
              aria-label="Chat conversation"
            >
              <div className="space-y-3 sm:space-y-4">
                {messages.length === 0 && !isStreaming ? (
                  <p className="text-muted-foreground text-center py-8 text-sm sm:text-base px-4">
                    Start a conversation by typing a message below
                  </p>
                ) : (
                  <>
                    {messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)}

                    {/* Show streaming message */}
                    {isStreaming && (
                      <StreamingMessage
                        content={streamingContent}
                        routingInfo={routingInfo}
                        isStreaming={isStreaming}
                      />
                    )}
                  </>
                )}
              </div>
            </ScrollArea>

            <ChatInput
              onSubmit={handleSubmit}
              disabled={!currentSessionId || isStreaming}
              isLoading={isStreaming}
              error={streamError ? streamError.message : null}
            />
          </CardContent>
        </Card>
      </main>
    </div>
  );
};