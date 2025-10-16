import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { chatApi, Message, ChatRequest } from '../api/chat';

export const useSession = (userId: string = 'web_user') => {
  return useQuery({
    queryKey: ['session', userId],
    queryFn: () => chatApi.createSession(userId),
    staleTime: Infinity,
  });
};

export const useChat = (sessionId: string | undefined, userId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (message: string) => {
      if (!sessionId) {
        throw new Error('No session available');
      }
      return chatApi.sendMessage({
        message,
        user_id: userId,
        session_id: sessionId,
      });
    },
    onSuccess: (data, message) => {
      const newMessage: Message = {
        id: Date.now().toString(),
        question: message,
        answer: data.response,
        timestamp: Date.now(),
      };

      queryClient.setQueryData<Message[]>(['messages', sessionId], (old = []) => [...old, newMessage]);
    },
  });
};