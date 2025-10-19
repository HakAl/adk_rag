export interface Message {
  id: string;
  question: string;
  answer: string;
  timestamp: number;
}

export interface SessionResponse {
  session_id: string;
  user_id: string;
}

export interface ChatRequest {
  message: string;
  user_id: string;
  session_id: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
}

export const chatApi = {
  createSession: async (userId: string = 'web_user'): Promise<SessionResponse> => {
    const response = await fetch('/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId }),
    });

    if (!response.ok) {
      throw new Error('Failed to create session');
    }

    return response.json();
  },

  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await fetch('/chat/coordinator', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    return response.json();
  },
};