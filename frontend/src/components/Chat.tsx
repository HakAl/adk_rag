import { useState, useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useSession, useChat } from '../hooks/useChat';
import { Message } from '../api/chat';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Send, Loader2, User, Bot } from 'lucide-react';

export const Chat = () => {
  const [input, setInput] = useState('');
  const userId = 'web_user';
  const scrollRef = useRef<HTMLDivElement>(null);

  const queryClient = useQueryClient();
  const { data: session, isLoading: sessionLoading, error: sessionError } = useSession(userId);
  const mutation = useChat(session?.session_id, userId);

  const messages = queryClient.getQueryData<Message[]>(['messages', session?.session_id]) || [];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages.length, mutation.isPending]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !session) return;

    if (input.trim().toLowerCase() === 'yabadabadoo!') {
      const easterEggMessage: Message = {
        id: `easter-${Date.now()}`,
        question: input.trim(),
        answer: "🦴 Yabba-Dabba-Doo! Fred Flintstone here! I'm an AI now because the stone tablet upgrade finally came through. Wilma says hi! 🦕",
        timestamp: Date.now()
      };

      const currentMessages = queryClient.getQueryData<Message[]>(['messages', session.session_id]) || [];
      queryClient.setQueryData(['messages', session.session_id], [...currentMessages, easterEggMessage]);
      setInput('');
      return;
    }

    mutation.mutate(input);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
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
              messages.map((msg) => (
                <div key={msg.id} className="space-y-2 animate-fade-in">
                  <div className="flex justify-end gap-2">
                    <div className="glass-message bg-gradient-to-br from-sky-400/90 to-cyan-500/90 text-white rounded-lg px-4 py-2 max-w-[80%] whitespace-pre-wrap transition-all hover:scale-[1.02] hover:shadow-lg">
                      {msg.question}
                    </div>
                    <div className="glass-avatar bg-gradient-to-br from-sky-400 to-cyan-500 text-white rounded-full p-2 h-8 w-8 flex items-center justify-center flex-shrink-0">
                      <User className="h-4 w-4" />
                    </div>
                  </div>
                  <div className="flex justify-start gap-2">
                    <div className="glass-avatar bg-gradient-to-br from-primary to-accent text-primary-foreground rounded-full p-2 h-8 w-8 flex items-center justify-center flex-shrink-0">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div className="glass-message bg-secondary/40 text-secondary-foreground rounded-lg px-4 py-2 max-w-[80%] whitespace-pre-wrap transition-all hover:scale-[1.02] hover:shadow-lg">
                      {msg.answer}
                    </div>
                  </div>
                </div>
              ))
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

        <form onSubmit={handleSubmit} className="flex gap-3 items-end flex-shrink-0">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Shift+Enter for new line)"
            disabled={mutation.isPending}
            className="flex-1 min-h-[80px] max-h-[200px] resize-y transition-all focus:scale-[1.01] focus:mr-1 glass-input"
            rows={3}
          />
          <Button type="submit" disabled={mutation.isPending || !session} size="icon" className="h-10 w-10 transition-transform hover:scale-110 active:scale-95 glass-button">
            {mutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>

        {mutation.isError && (
          <p className="text-red-400 text-sm mt-2 animate-fade-in">Error: {mutation.error.message}</p>
        )}
      </CardContent>
    </Card>
  );
};