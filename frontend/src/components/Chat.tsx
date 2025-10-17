import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useSession, useChat } from '../hooks/useChat';
import { Message } from '../api/chat';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Send, Loader2 } from 'lucide-react';

export const Chat = () => {
  const [input, setInput] = useState('');
  const userId = 'web_user';

  const queryClient = useQueryClient();
  const { data: session, isLoading: sessionLoading, error: sessionError } = useSession(userId);
  const mutation = useChat(session?.session_id, userId);

  const messages = queryClient.getQueryData<Message[]>(['messages', session?.session_id]) || [];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !session) return;

    mutation.mutate(input);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter, but allow Shift+Enter for new lines
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  if (sessionLoading) {
    return (
      <Card>
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
      <Card className="border-red-500 bg-red-950/20">
        <CardContent className="p-6">
          <p className="text-red-400">Failed to create session: {sessionError.message}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Chat</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[500px] mb-4 pr-4">
          <div className="space-y-4">
            {messages.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">
                Start a conversation by typing a message below
              </p>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className="space-y-2">
                  <div className="flex justify-end">
                    <div className="bg-blue-600 text-white rounded-lg px-4 py-2 max-w-[80%] whitespace-pre-wrap">
                      {msg.question}
                    </div>
                  </div>
                  <div className="flex justify-start">
                    <div className="bg-secondary text-secondary-foreground rounded-lg px-4 py-2 max-w-[80%] whitespace-pre-wrap">
                      {msg.answer}
                    </div>
                  </div>
                </div>
              ))
            )}

            {mutation.isPending && (
              <div className="flex justify-start">
                <div className="bg-secondary/60 text-secondary-foreground rounded-lg px-4 py-2 flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Thinking...</span>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        <form onSubmit={handleSubmit} className="flex gap-2 items-end">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Shift+Enter for new line)"
            disabled={mutation.isPending}
            className="flex-1 min-h-[80px] max-h-[200px] resize-y"
            rows={3}
          />
          <Button type="submit" disabled={mutation.isPending || !session} size="icon" className="h-10 w-10">
            {mutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>

        {mutation.isError && (
          <p className="text-red-400 text-sm mt-2">Error: {mutation.error.message}</p>
        )}
      </CardContent>
    </Card>
  );
};