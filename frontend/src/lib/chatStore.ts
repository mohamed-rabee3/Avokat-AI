interface Message {
  id: string;
  content: string;
  type: 'user' | 'assistant';
  timestamp: Date;
  attachments?: File[];
}

interface ChatSession {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

class ChatStore {
  private sessions: ChatSession[] = [];
  private currentSessionId: string | null = null;

  constructor() {
    this.loadFromStorage();
  }

  private loadFromStorage() {
    try {
      const stored = localStorage.getItem('chat-sessions');
      if (stored) {
        const parsed = JSON.parse(stored);
        this.sessions = parsed.map((session: any) => ({
          ...session,
          createdAt: new Date(session.createdAt),
          updatedAt: new Date(session.updatedAt),
          messages: session.messages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
          })),
        }));
      }
    } catch (error) {
      console.error('Failed to load chat sessions from storage:', error);
    }
  }

  private saveToStorage() {
    try {
      localStorage.setItem('chat-sessions', JSON.stringify(this.sessions));
    } catch (error) {
      console.error('Failed to save chat sessions to storage:', error);
    }
  }

  createNewSession(): string {
    const sessionId = `chat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const session: ChatSession = {
      id: sessionId,
      title: 'New Chat',
      messages: [{
        id: `msg-${Date.now()}`,
        content: 'Hello! How can I help you today?',
        type: 'assistant',
        timestamp: new Date(),
      }],
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    this.sessions.unshift(session);
    this.currentSessionId = sessionId;
    this.saveToStorage();
    return sessionId;
  }

  getCurrentSession(): ChatSession | null {
    if (!this.currentSessionId) {
      return null;
    }
    return this.sessions.find(session => session.id === this.currentSessionId) || null;
  }

  setCurrentSession(sessionId: string): ChatSession | null {
    const session = this.sessions.find(session => session.id === sessionId);
    if (session) {
      this.currentSessionId = sessionId;
      return session;
    }
    return null;
  }

  addMessage(message: Omit<Message, 'id' | 'timestamp'>): Message | null {
    const currentSession = this.getCurrentSession();
    if (!currentSession) {
      return null;
    }

    const newMessage: Message = {
      ...message,
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    };

    currentSession.messages.push(newMessage);
    currentSession.updatedAt = new Date();

    // Update title based on first user message
    if (message.type === 'user' && currentSession.messages.length === 2) {
      currentSession.title = message.content.slice(0, 50) + (message.content.length > 50 ? '...' : '');
    }

    this.saveToStorage();
    return newMessage;
  }

  getAllSessions(): ChatSession[] {
    return [...this.sessions].sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());
  }

  deleteSession(sessionId: string): boolean {
    const index = this.sessions.findIndex(session => session.id === sessionId);
    if (index !== -1) {
      this.sessions.splice(index, 1);
      if (this.currentSessionId === sessionId) {
        this.currentSessionId = null;
      }
      this.saveToStorage();
      return true;
    }
    return false;
  }

  getCurrentSessionId(): string | null {
    return this.currentSessionId;
  }
}

export const chatStore = new ChatStore();
export type { Message, ChatSession };