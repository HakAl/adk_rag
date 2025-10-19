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

export interface StreamEvent {
  type: 'routing' | 'content' | 'done' | 'error';
  data: any;
}

export interface RoutingInfo {
  agent: string;
  agent_name: string;
  confidence: number;
  reasoning?: string;
}

export const chatApi = {
  createSession: async (userId: string = 'web_user'): Promise<SessionResponse> => {
    // FIXED: Use coordinator endpoint to match backend flow
    const response = await fetch('/sessions/coordinator', {
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

  streamMessage: async (
    request: ChatRequest,
    onEvent: (event: StreamEvent) => void
  ): Promise<void> => {
    const response = await fetch('/chat/coordinator/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error('Failed to stream message');
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        console.log('🔥 Raw chunk received, size:', value?.length, 'done:', done);

        if (done) break;

        // Decode the chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });
        console.log('📦 Buffer now:', buffer.length, 'chars');

        // Split on double newline (SSE event separator)
        const events = buffer.split('\n\n');

        // Keep the last incomplete event in buffer
        buffer = events.pop() || '';

        // Process complete events
        for (const event of events) {
          const lines = event.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = line.slice(6);
                const parsedEvent: StreamEvent = JSON.parse(data);
                onEvent(parsedEvent);
              } catch (e) {
                console.error('Failed to parse SSE event:', line, e);
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },
};