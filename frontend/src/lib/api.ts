/**
 * API service for connecting to the backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Session {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  token_count: number;
  created_at: string;
}

export interface ChatHistory {
  session_id: number;
  messages: Message[];
  total_count: number;
}

export interface ChatResponse {
  response: string;
  sources: Array<{
    type: string;
    name?: string;
    entity_type?: string;
    relationship_type?: string;
    language?: string;
  }>;
}

export interface IngestResponse {
  status: string;
  session_id: number;
  file_name: string;
  size_bytes: number;
  chunks: number;
  nodes_created: number;
  relationships_created: number;
  batch_id: string;
  session_stats?: any;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      // Handle responses with no content (like DELETE 204)
      if (response.status === 204 || response.headers.get('content-length') === '0') {
        return undefined as T;
      }

      // Only try to parse JSON if there's content
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }

      return undefined as T;
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Sessions API
  async createSession(name?: string): Promise<Session> {
    return this.request<Session>('/sessions', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  async getSessions(): Promise<Session[]> {
    return this.request<Session[]>('/sessions');
  }

  async getSession(sessionId: number): Promise<Session> {
    return this.request<Session>(`/sessions/${sessionId}`);
  }

  async updateSession(sessionId: number, name: string): Promise<Session> {
    return this.request<Session>(`/sessions/${sessionId}`, {
      method: 'PUT',
      body: JSON.stringify({ name }),
    });
  }

  async deleteSession(sessionId: number): Promise<void> {
    await this.request<void>(`/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  // Chat API
  async sendMessage(
    sessionId: number,
    message: string,
    stream: boolean = true
  ): Promise<ChatResponse | ReadableStream> {
    const endpoint = stream ? '/chat' : '/chat/non-streaming';
    
    if (stream) {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: message,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      return response.body!;
    } else {
      return this.request<ChatResponse>(endpoint, {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionId,
          message: message,
        }),
      });
    }
  }

  async getChatHistory(sessionId: number, limit: number = 50): Promise<ChatHistory> {
    return this.request<ChatHistory>(`/chat/history/${sessionId}?limit=${limit}`);
  }

  // File upload API
  async uploadFile(sessionId: number, file: File): Promise<IngestResponse> {
    const formData = new FormData();
    formData.append('session_id', sessionId.toString());
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/ingest`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health');
  }
}

export const apiService = new ApiService();
export default apiService;
