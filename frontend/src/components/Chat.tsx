import { useState, useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';
import ReactMarkdown from 'react-markdown';
import { useSession, useChat } from '../hooks/useChat';
import { Message } from '../api/chat';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Send, Loader2, User, Bot, Copy, Check } from 'lucide-react';

export const Chat = () => {
  const [input, setInput] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
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

  const formatTimestamp = (timestamp: number) => {
    return format(new Date(timestamp), 'h:mm a');
  };

  const handleCopy = async (messageId: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(messageId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

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

    if (input.trim().toLowerCase() === 'giggity') {
      const easterEggMessage: Message = {
        id: `easter-${Date.now()}`,
        question: input.trim(),
        answer: `# 🎉 Giggity Giggity Goo!

**Congratulations!** You've unlocked the *secret giggity counter*.

## Current Stats:
- **Giggities given**: ∞
- **Alright level**: Maximum
- **Coolness factor**: Off the charts

\`Warning: Excessive giggity may cause spontaneous laughter\`

> "Who else but Quagmire?" - Everyone`,
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
                    <div className="flex flex-col items-end gap-1 max-w-[80%]">
                      <div className="glass-message bg-gradient-to-br from-sky-400/90 to-cyan-500/90 text-white rounded-lg px-4 py-2 w-full whitespace-pre-wrap transition-all hover:scale-[1.02] hover:shadow-lg">
                        {msg.question}
                      </div>
                      <span className="text-xs text-muted-foreground px-1">
                        {formatTimestamp(msg.timestamp)}
                      </span>
                    </div>
                    <div className="glass-avatar bg-gradient-to-br from-sky-400 to-cyan-500 text-white rounded-full p-2 h-8 w-8 flex items-center justify-center flex-shrink-0">
                      <User className="h-4 w-4" />
                    </div>
                  </div>
                  <div className="flex justify-start gap-2">
                    <div className="glass-avatar bg-gradient-to-br from-primary to-accent text-primary-foreground rounded-full p-2 h-8 w-8 flex items-center justify-center flex-shrink-0">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div className="flex flex-col items-start gap-1 max-w-[80%]">
                      <div className="relative group glass-message bg-secondary/40 text-secondary-foreground rounded-lg px-4 py-2 w-full transition-all hover:scale-[1.02] hover:shadow-lg">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="absolute top-2 right-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() => handleCopy(msg.id, msg.answer)}
                        >
                          {copiedId === msg.id ? (
                            <Check className="h-3 w-3 text-green-500" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </Button>
                        <ReactMarkdown
                          className="markdown-content"
                          components={{
                            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                            code: ({ className, children }) => {
                              const isInline = !className;
                              return isInline ? (
                                <code className="bg-primary/10 text-primary px-1.5 py-0.5 rounded text-sm font-mono">
                                  {children}
                                </code>
                              ) : (
                                <code className="block bg-primary/10 text-primary p-3 rounded my-2 text-sm font-mono overflow-x-auto">
                                  {children}
                                </code>
                              );
                            },
                            ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                            ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                            li: ({ children }) => <li className="ml-2">{children}</li>,
                            h1: ({ children }) => <h1 className="text-xl font-bold mb-2 mt-3">{children}</h1>,
                            h2: ({ children }) => <h2 className="text-lg font-bold mb-2 mt-3">{children}</h2>,
                            h3: ({ children }) => <h3 className="text-base font-bold mb-2 mt-2">{children}</h3>,
                            strong: ({ children }) => <strong className="font-bold text-primary">{children}</strong>,
                            em: ({ children }) => <em className="italic">{children}</em>,
                            blockquote: ({ children }) => (
                              <blockquote className="border-l-4 border-primary/30 pl-4 my-2 italic text-muted-foreground">
                                {children}
                              </blockquote>
                            ),
                            a: ({ href, children }) => (
                              <a href={href} className="text-primary hover:underline" target="_blank" rel="noopener noreferrer">
                                {children}
                              </a>
                            ),
                          }}
                        >
                          {msg.answer}
                        </ReactMarkdown>
                      </div>
                      <span className="text-xs text-muted-foreground px-1">
                        {formatTimestamp(msg.timestamp)}
                      </span>
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