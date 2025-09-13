import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, User, Bot, Upload, FileText, ChevronDown, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';
import { apiService, ChatResponse, Message as ApiMessage } from '@/lib/api';

interface ChatInterfaceProps {
  sessionId?: string;
}

interface BackendSession {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
}

interface LocalMessage {
  id: string;
  content: string;
  type: 'user' | 'assistant';
  timestamp: Date;
  sources?: Array<{
    type: string;
    name?: string;
    entity_type?: string;
    relationship_type?: string;
    language?: string;
  }>;
}

export function ChatInterface({ sessionId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [backendSessionId, setBackendSessionId] = useState<number | null>(null);
  const [sessionName, setSessionName] = useState<string>('New Chat');
  const [isInitializing, setIsInitializing] = useState(true);
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // Initialize or load session
  useEffect(() => {
    const initializeSession = async () => {
      // Prevent multiple initializations
      if (backendSessionId !== null) {
        return;
      }

      try {
        setIsInitializing(true);
        let session: BackendSession;
        
        if (sessionId && !isNaN(Number(sessionId))) {
          // Load existing session
          session = await apiService.getSession(Number(sessionId));
          setBackendSessionId(session.id);
          setSessionName(session.name || `Session ${session.id}`);
          
          // Load chat history
          const history = await apiService.getChatHistory(session.id);
          const localMessages: LocalMessage[] = history.messages.map(msg => ({
            id: `msg-${msg.id}`,
            content: msg.content,
            type: msg.role,
            timestamp: new Date(msg.created_at)
          }));
          setMessages(localMessages);
        } else {
          // Don't automatically create a new session - let user click "New Chat" button
          // This prevents unwanted session creation after deletion
          setMessages([]);
          setSessionName('Welcome');
        }
      } catch (error) {
        console.error('Failed to initialize session:', error);
        toast({
          title: "Error",
          description: "Failed to initialize chat session. Please refresh the page.",
          variant: "destructive",
        });
      } finally {
        setIsInitializing(false);
      }
    };

    initializeSession();
  }, [sessionId, toast, backendSessionId]);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !backendSessionId || isLoading) return;

    const userMessage: LocalMessage = {
      id: `msg-${Date.now()}`,
      content: inputValue.trim(),
      type: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Send message to backend
      const response = await apiService.sendMessage(backendSessionId, userMessage.content, false) as ChatResponse;
      
      const assistantMessage: LocalMessage = {
        id: `msg-${Date.now()}-assistant`,
        content: response.response,
        type: 'assistant',
        timestamp: new Date(),
        sources: response.sources,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFiles.length || !backendSessionId || isUploading) return;

    setIsUploading(true);
    
    try {
      for (const file of selectedFiles) {
        const response = await apiService.uploadFile(backendSessionId, file);
        
        toast({
          title: "File Uploaded",
          description: `${file.name} processed successfully. Created ${response.nodes_created} entities and ${response.relationships_created} relationships.`,
        });
      }
      
      setSelectedFiles([]);
    } catch (error) {
      console.error('Failed to upload file:', error);
      toast({
        title: "Upload Error",
        description: "Failed to upload file. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    setSelectedFiles(prev => [...prev, ...files]);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const toggleSources = (messageId: string) => {
    setExpandedSources(prev => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  const hasUploadedFiles = messages.some(msg => msg.type === 'assistant' && msg.sources && msg.sources.length > 0);

  // Show loading state while initializing
  if (isInitializing) {
    return (
      <div className="flex flex-col h-full items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        <p className="mt-4 text-muted-foreground">Initializing chat...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="border-b bg-card p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-lg">{sessionName}</h2>
            <p className="text-sm text-muted-foreground">
              {hasUploadedFiles ? "Ready to answer questions about your documents" : "Upload documents to enable chat"}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
            >
              <Upload className="h-4 w-4 mr-2" />
              Upload PDF
            </Button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">
                {backendSessionId ? "Welcome to Avokat AI" : "Start a New Chat"}
              </p>
              <p className="text-sm">
                {backendSessionId 
                  ? "Upload legal documents to start asking questions about their content."
                  : "Click 'New Chat' in the sidebar to begin a conversation."
                }
              </p>
            </div>
          )}
          
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                'flex items-start gap-3 animate-fade-in',
                message.type === 'user' ? 'flex-row-reverse' : 'flex-row'
              )}
            >
              <div className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
                message.type === 'user' 
                  ? 'bg-primary text-primary-foreground' 
                  : 'bg-muted text-muted-foreground'
              )}>
                {message.type === 'user' ? (
                  <User className="w-4 h-4" />
                ) : (
                  <Bot className="w-4 h-4" />
                )}
              </div>
              
              <div className={cn(
                'max-w-[80%] rounded-lg p-3 shadow-sm animate-scale-in',
                message.type === 'user' 
                  ? 'chat-message-user' 
                  : 'chat-message-assistant'
              )}>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                
                {/* Sources */}
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-border/50">
                    <button
                      onClick={() => toggleSources(message.id)}
                      className="flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors mb-2"
                    >
                      {expandedSources.has(message.id) ? (
                        <ChevronDown className="h-3 w-3" />
                      ) : (
                        <ChevronRight className="h-3 w-3" />
                      )}
                      Sources ({message.sources.length})
                    </button>
                    {expandedSources.has(message.id) && (
                      <div className="space-y-1 animate-fade-in">
                        {message.sources.map((source, index) => (
                          <div
                            key={index}
                            className="text-xs bg-muted/50 rounded px-2 py-1"
                          >
                            <span className="font-medium">{source.type}:</span>{' '}
                            {source.name || source.entity_type || source.relationship_type}
                            {source.language && (
                              <span className="text-muted-foreground ml-1">({source.language})</span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                
                <div className="text-xs opacity-60 mt-1">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          
          {/* Loading indicator */}
          {isLoading && (
            <div className="flex items-start gap-3 animate-fade-in">
              <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 bg-muted text-muted-foreground">
                <Bot className="w-4 h-4" />
              </div>
              <div className="chat-message-assistant rounded-lg p-3 shadow-sm">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-current rounded-full animate-pulse"></div>
                  <div className="w-2 h-2 bg-current rounded-full animate-pulse delay-75"></div>
                  <div className="w-2 h-2 bg-current rounded-full animate-pulse delay-150"></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* File Preview */}
      {selectedFiles.length > 0 && (
        <div className="border-t p-2 bg-muted/50 animate-fade-in">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium">Selected Files:</p>
            <Button
              size="sm"
              onClick={handleFileUpload}
              disabled={isUploading}
            >
              {isUploading ? "Uploading..." : "Upload Files"}
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center gap-2 bg-background rounded px-2 py-1 text-xs hover-scale"
              >
                <Paperclip className="w-3 h-3" />
                <span>{file.name}</span>
                <button
                  onClick={() => removeFile(index)}
                  className="ml-1 text-destructive hover:text-destructive/80 transition-colors"
                  disabled={isUploading}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chat Input */}
      {backendSessionId && (
        <div className="border-t p-4">
          <div className="flex gap-2 items-end">
            <div className="flex-1 relative">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask a question about your documents..."
                className="chat-input pr-12"
                disabled={isLoading || isUploading}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8 p-0 hover-scale"
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading || isUploading}
              >
                <Paperclip className="h-4 w-4" />
              </Button>
            </div>
            
            <Button
              onClick={handleSendMessage}
              disabled={(!inputValue.trim() && selectedFiles.length === 0) || isLoading || isUploading}
              className="px-4 hover-scale"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleFileSelect}
            accept=".pdf"
          />
        </div>
      )}
    </div>
  );
}