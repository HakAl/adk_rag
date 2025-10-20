import { useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Message } from '../api/backend/chat.ts';
import { useEasterEggs } from './useEasterEggs';

interface UseMessageManagerReturn {
  messages: Message[];
  easterEggMessages: Message[];
  addOptimisticMessage: (question: string) => Message;
  clearEasterEggs: () => void;
  handleEasterEgg: (input: string) => boolean;
}

export const useMessageManager = (sessionId: string): UseMessageManagerReturn => {
  const queryClient = useQueryClient();
  const { checkEasterEgg } = useEasterEggs();
  const [easterEggMessages, setEasterEggMessages] = useState<Message[]>([]);

  const backendMessages = queryClient.getQueryData<Message[]>(['messages', sessionId]) || [];
  const messages = [...backendMessages, ...easterEggMessages];

  const addOptimisticMessage = useCallback((question: string): Message => {
    const optimisticMessage: Message = {
      id: `optimistic-${Date.now()}`,
      question,
      answer: '',
      timestamp: Date.now(),
    };

    queryClient.setQueryData<Message[]>(['messages', sessionId], (old = []) => {
      return [...old, optimisticMessage];
    });

    return optimisticMessage;
  }, [sessionId, queryClient]);

  const clearEasterEggs = useCallback(() => {
    setEasterEggMessages([]);
  }, []);

  const handleEasterEgg = useCallback((input: string): boolean => {
    const easterEggMessage = checkEasterEgg(input);
    if (easterEggMessage) {
      setEasterEggMessages(prev => [...prev, easterEggMessage]);
      return true;
    }
    return false;
  }, [checkEasterEgg]);

  return {
    messages,
    easterEggMessages,
    addOptimisticMessage,
    clearEasterEggs,
    handleEasterEgg,
  };
};