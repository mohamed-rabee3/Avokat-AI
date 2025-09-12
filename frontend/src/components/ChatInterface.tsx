import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, User, Bot } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import { chatStore, Message } from '@/lib/chatStore';
import { useToast } from '@/hooks/use-toast';

interface ChatInterfaceProps {
  sessionId?: string;
}

export function ChatInterface({ sessionId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // Load messages when sessionId changes
  useEffect(() => {
    if (sessionId) {
      const session = chatStore.setCurrentSession(sessionId);
      if (session) {
        setMessages(session.messages);
      }
    } else {
      // Create new session if none provided
      const newSessionId = chatStore.createNewSession();
      const session = chatStore.getCurrentSession();
      if (session) {
        setMessages(session.messages);
      }
    }
  }, [sessionId]);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() && selectedFiles.length === 0) return;

    const userMessage = chatStore.addMessage({
      content: inputValue,
      type: 'user',
      attachments: selectedFiles.length > 0 ? selectedFiles : undefined,
    });

    if (!userMessage) {
      toast({
        title: "Error",
        description: "Failed to send message. Please try again.",
        variant: "destructive",
      });
      return;
    }

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setSelectedFiles([]);
    setIsLoading(true);

    // Simulate AI response with a delay
    setTimeout(() => {
      const responses = [
        "I understand your question. Let me help you with that.",
        "That's an interesting point. Here's what I think about it...",
        "I can help you with that. Based on what you've shared...",
        "Thank you for sharing those details. Let me provide some guidance.",
        "I've reviewed your message and attached files. Here's my response...",
      ];
      
      const randomResponse = responses[Math.floor(Math.random() * responses.length)];
      
      const assistantMessage = chatStore.addMessage({
        content: randomResponse,
        type: 'assistant',
      });

      if (assistantMessage) {
        setMessages(prev => [...prev, assistantMessage]);
      }
      setIsLoading(false);
    }, 1000 + Math.random() * 2000);
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

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="border-b bg-card p-4">
        <h2 className="font-semibold text-lg">Chat Assistant</h2>
        <p className="text-sm text-muted-foreground">Ask me anything!</p>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
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
                <p className="text-sm leading-relaxed">{message.content}</p>
                {message.attachments && message.attachments.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {message.attachments.map((file, index) => (
                      <div
                        key={index}
                        className="text-xs opacity-80 flex items-center gap-1"
                      >
                        <Paperclip className="w-3 h-3" />
                        {file.name}
                      </div>
                    ))}
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
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chat Input */}
      <div className="border-t p-4">
        <div className="flex gap-2 items-end">
          <div className="flex-1 relative">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              className="chat-input pr-12"
              disabled={isLoading}
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8 p-0 hover-scale"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
            >
              <Paperclip className="h-4 w-4" />
            </Button>
          </div>
          
          <Button
            onClick={handleSendMessage}
            disabled={(!inputValue.trim() && selectedFiles.length === 0) || isLoading}
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
          accept="image/*,.pdf,.doc,.docx,.txt,.csv,.json"
        />
      </div>
    </div>
  );
}