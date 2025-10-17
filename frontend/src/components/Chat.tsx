import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useSession, useChat } from '../hooks/useChat';
import { Message } from '../api/chat';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Loader2, Bot } from 'lucide-react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { useEasterEggs } from '../hooks/useEasterEggs';

export const Chat = () => {
  const userId = 'web_user';
  const scrollRef = useRef<HTMLDivElement>(null);
  const [easterEggMessages, setEasterEggMessages] = useState<Message[]>([]);

  const queryClient = useQueryClient();
  const { data: session, isLoading: sessionLoading, error: sessionError } = useSession(userId);
  const mutation = useChat(session?.session_id, userId);
  const { checkEasterEgg } = useEasterEggs();

  const backendMessages = queryClient.getQueryData<Message[]>(['messages', session?.session_id]) || [];
  const messages = [...backendMessages, ...easterEggMessages];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages.length, mutation.isPending]);

  const handleSubmit = (input: string) => {
    if (!session) return;

    // Check for easter eggs
    const easterEggMessage = checkEasterEgg(input);
    if (easterEggMessage) {
      setEasterEggMessages(prev => [...prev, easterEggMessage]);
      return;
    }

    // Normal message processing
    mutation.mutate(input);
  };

  if (sessionLoading) {
    return (
      <Card className="glass-card">
        <CardContent className="p-6">
          <div className="flex items-center justify-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin text-primary" />
            <p className="text-foreground">Initializing chat session...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (sessionError) {
    return (
      <Card className="glass-card border-red-500/50 bg-red-950/20">
        <CardContent className="p-6">
          <p className="text-red-400">Failed to create session: {sessionError.message}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full h-[calc(100vh-8rem)] flex flex-col glass-card gradient-border">
      <CardHeader className="flex-shrink-0">
        <CardTitle className="gradient-text">Chat</CardTitle>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col min-h-0">
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
          disabled={!session}
          isLoading={mutation.isPending}
          error={mutation.isError ? mutation.error.message : null}
        />
      </CardContent>
    </Card>
  );
};