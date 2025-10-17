import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useSession, useChat } from '../hooks/useChat';
import { useSessionStorage, sessionStorage } from '../hooks/useSessionStorage';
import { Message } from '../api/chat';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Loader2, Bot, Menu } from 'lucide-react';
import { Button } from './ui/button';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { SessionSidebar } from './SessionSidebar';
import { useEasterEggs } from '../hooks/useEasterEggs';

export const Chat = () => {
  const userId = 'web_user';
  const scrollRef = useRef<HTMLDivElement>(null);
  const [easterEggMessages, setEasterEggMessages] = useState<Message[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');

  const queryClient = useQueryClient();
  const { data: session, isLoading: sessionLoading, error: sessionError, refetch: refetchSession } = useSession(userId);
  const mutation = useChat(currentSessionId || session?.session_id, userId);
  const { checkEasterEgg } = useEasterEggs();
  const {
    sessions,
    createSession,
    updateSessionMetadata,
    deleteSession: deleteStoredSession,
    refreshSessions
  } = useSessionStorage();

  // Initialize session from localStorage or create new one
  useEffect(() => {
    if (sessionLoading) return;

    const storedSessionId = sessionStorage.getActiveSessionId();
    const storedSessions = sessionStorage.getSessions();

    if (storedSessionId && storedSessions.find(s => s.sessionId === storedSessionId)) {
      // Load existing session from localStorage
      setCurrentSessionId(storedSessionId);
      const storedMessages = sessionStorage.getMessages(storedSessionId);
      // Sort by timestamp to ensure chronological order (oldest first)
      const sortedMessages = [...storedMessages].sort((a, b) => a.timestamp - b.timestamp);
      queryClient.setQueryData<Message[]>(['messages', storedSessionId], sortedMessages);
    } else if (session?.session_id) {
      // Use backend session and register it in localStorage
      const newSessionId = session.session_id;
      setCurrentSessionId(newSessionId);
      createSession(newSessionId);
      sessionStorage.setActiveSessionId(newSessionId);
    }
  }, [session, sessionLoading, createSession, queryClient]);

  const backendMessages = queryClient.getQueryData<Message[]>(['messages', currentSessionId]) || [];

  // Combine messages while maintaining order - backend messages include both questions and answers
  const messages = [...backendMessages, ...easterEggMessages];

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (currentSessionId && messages.length > 0) {
      sessionStorage.saveMessages(currentSessionId, messages);

      // Update session metadata
      const firstUserMessage = messages[0]?.question;
      updateSessionMetadata(currentSessionId, messages.length, firstUserMessage);
    }
  }, [messages.length, currentSessionId]); // Removed updateSessionMetadata from deps - we only care about message count changes

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages.length, mutation.isPending]);

  const handleNewSession = async () => {
    // Create new backend session
    const { data: newSession } = await refetchSession();

    if (newSession?.session_id) {
      setCurrentSessionId(newSession.session_id);
      createSession(newSession.session_id);
      sessionStorage.setActiveSessionId(newSession.session_id);
      queryClient.setQueryData<Message[]>(['messages', newSession.session_id], []);
      setEasterEggMessages([]);
      setSidebarOpen(false);
    }
  };

  const handleSelectSession = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    sessionStorage.setActiveSessionId(sessionId);

    // Load messages from localStorage and ensure proper order
    const storedMessages = sessionStorage.getMessages(sessionId);
    // Sort by timestamp to ensure chronological order (oldest first)
    const sortedMessages = [...storedMessages].sort((a, b) => a.timestamp - b.timestamp);
    queryClient.setQueryData<Message[]>(['messages', sessionId], sortedMessages);
    setEasterEggMessages([]);
    setSidebarOpen(false);
  };

  const handleDeleteSession = (sessionId: string) => {
    // First, get the current sessions list from localStorage to get accurate count
    const currentSessions = sessionStorage.getSessions();

    // Delete the session
    deleteStoredSession(sessionId);
    queryClient.removeQueries({ queryKey: ['messages', sessionId] });

    // If deleting active session, handle accordingly
    if (sessionId === currentSessionId) {
      // Check if there are other sessions remaining (excluding the one we just deleted)
      const remainingSessions = currentSessions.filter(s => s.sessionId !== sessionId);

      if (remainingSessions.length > 0) {
        // Switch to the first remaining session
        handleSelectSession(remainingSessions[0].sessionId);
      } else {
        // No sessions left, create a new one
        handleNewSession();
      }
    }
  };

  const handleSubmit = (input: string) => {
    if (!currentSessionId) return;

    // Check for easter eggs
    const easterEggMessage = checkEasterEgg(input);
    if (easterEggMessage) {
      setEasterEggMessages(prev => [...prev, easterEggMessage]);
      return;
    }

    // Clear easter eggs when asking a real question
    setEasterEggMessages([]);

    // Add optimistic message immediately
    const optimisticMessage: Message = {
      id: `temp-${Date.now()}`,
      question: input,
      answer: '', // Will be filled when response comes back
      timestamp: Date.now(),
    };

    queryClient.setQueryData<Message[]>(['messages', currentSessionId], (old = []) => {
      return [...old, optimisticMessage];
    });

    // Normal message processing
    mutation.mutate(input);
  };

  if (sessionLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Card className="glass-card">
          <CardContent className="p-6">
            <div className="flex items-center justify-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
              <p className="text-foreground">Initializing chat session...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (sessionError) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Card className="glass-card border-red-500/50 bg-red-950/20">
          <CardContent className="p-6">
            <p className="text-red-400">Failed to create session: {sessionError.message}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex gap-4 h-full">
      <SessionSidebar
        sessions={sessions}
        activeSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex-1 flex flex-col min-w-0 h-full">
        <Card className="h-full flex flex-col glass-card gradient-border">
          <CardHeader className="flex-shrink-0 flex flex-row items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden"
            >
              <Menu className="h-5 w-5" />
            </Button>
            <CardTitle className="gradient-text">Chat</CardTitle>
          </CardHeader>

          <CardContent className="flex-1 flex flex-col min-h-0 pb-4">
            <ScrollArea ref={scrollRef} className="flex-1 mb-4 pr-4">
              <div className="space-y-4">
                {messages.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">
                    Start a conversation by typing a message below
                  </p>
                ) : (
                  messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
                )}

                {mutation.isPending && (
                  <div className="flex justify-start gap-2 animate-fade-in">
                    <div className="glass-avatar bg-gradient-to-br from-primary to-accent text-primary-foreground rounded-full p-2 h-8 w-8 flex items-center justify-center flex-shrink-0">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div className="glass-message bg-secondary/30 text-secondary-foreground rounded-lg px-4 py-2 flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="animate-pulse">Thinking...</span>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            <ChatInput
              onSubmit={handleSubmit}
              disabled={!currentSessionId}
              isLoading={mutation.isPending}
              error={mutation.isError ? mutation.error.message : null}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};