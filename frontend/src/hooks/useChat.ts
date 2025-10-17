import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { chatApi, Message, ChatRequest } from '../api/chat';
import { sessionStorage } from './useSessionStorage';

export const useSession = (userId: string = 'web_user') => {
  return useQuery({
    queryKey: ['session', userId],
    queryFn: () => chatApi.createSession(userId),
    staleTime: Infinity,
    // Don't automatically refetch - we'll manually trigger when needed
    refetchOnMount: false,
    refetchOnWindowFocus: false,
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
      // Update the optimistic message with the actual response
      queryClient.setQueryData<Message[]>(['messages', sessionId], (old = []) => {
        // Find the most recent optimistic message for this question
        const optimisticIndex = [...old].reverse().findIndex(msg =>
          msg.question === message && msg.answer === ''
        );

        // Convert reversed index back to normal index
        const actualIndex = optimisticIndex !== -1 ? old.length - 1 - optimisticIndex : -1;

        let updated: Message[];
        if (actualIndex !== -1) {
          // Update the existing optimistic message in place
          updated = [...old];
          updated[actualIndex] = {
            ...updated[actualIndex],
            id: Date.now().toString(),
            answer: data.response,
          };
        } else {
          // If no optimistic message found, add a new one at the end (fallback)
          const newMessage: Message = {
            id: Date.now().toString(),
            question: message,
            answer: data.response,
            timestamp: Date.now(),
          };
          updated = [...old, newMessage];
        }

        // Save to localStorage
        if (sessionId) {
          sessionStorage.saveMessages(sessionId, updated);
        }

        return updated;
      });
    },
  });
};