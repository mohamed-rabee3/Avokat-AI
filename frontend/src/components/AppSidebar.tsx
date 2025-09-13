import React, { useState, useEffect } from 'react';
import { MessageCircle, History, Settings, HelpCircle, Plus, Trash2 } from 'lucide-react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ThemeToggle } from '@/components/ThemeToggle';
import { cn } from '@/lib/utils';
import { chatStore, ChatSession } from '@/lib/chatStore';
import { useToast } from '@/hooks/use-toast';
import { apiService, Session as BackendSession } from '@/lib/api';

const mainItems = [
  { title: 'New Chat', url: '/', icon: MessageCircle },
  { title: 'Chat History', url: '/history', icon: History },
];

const settingsItems = [
  { title: 'Settings', url: '/settings', icon: Settings },
  { title: 'Help', url: '/help', icon: HelpCircle },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const location = useLocation();
  const navigate = useNavigate();
  const currentPath = location.pathname;
  const { toast } = useToast();
  
  const [chatSessions, setChatSessions] = useState<BackendSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const isCollapsed = state === 'collapsed';
  const isActive = (path: string) => currentPath === path;

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      setIsLoading(true);
      const sessions = await apiService.getSessions();
      setChatSessions(sessions);
    } catch (error) {
      console.error('Failed to load sessions:', error);
      toast({
        title: "Error",
        description: "Failed to load chat sessions",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = async () => {
    try {
      setIsLoading(true);
      const session = await apiService.createSession('New Chat');
      await loadSessions();
      setCurrentSessionId(session.id);
      navigate(`/chat/${session.id}`);
      toast({
        title: "New chat created",
        description: "Started a new conversation",
      });
    } catch (error) {
      console.error('Failed to create session:', error);
      toast({
        title: "Error",
        description: "Failed to create new chat session",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteSession = async (sessionId: number, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    // Note: Backend doesn't have delete session endpoint yet
    // For now, just show a message
    toast({
      title: "Delete not available",
      description: "Session deletion is not yet implemented",
      variant: "destructive",
    });
  };

  const handleSessionClick = (sessionId: number) => {
    setCurrentSessionId(sessionId);
    navigate(`/chat/${sessionId}`);
  };

  return (
    <Sidebar
      className="border-r shadow-[var(--shadow-sidebar)]"
      collapsible="icon"
    >
      <SidebarContent>
        {/* Header */}
        <div className="p-4 border-b border-sidebar-border">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center">
                <MessageCircle className="w-4 h-4 text-primary-foreground" />
              </div>
              {!isCollapsed && (
                <span className="font-semibold text-sidebar-foreground">Chat App</span>
              )}
            </div>
            {!isCollapsed && <ThemeToggle />}
          </div>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <Button
            onClick={handleNewChat}
            disabled={isLoading}
            className={cn(
              'w-full justify-start gap-2 hover-scale',
              isCollapsed && 'px-2 justify-center'
            )}
            variant="outline"
          >
            <Plus className="w-4 h-4" />
            {!isCollapsed && <span>{isLoading ? "Creating..." : "New Chat"}</span>}
          </Button>
        </div>

        {/* Chat History */}
        {!isCollapsed && chatSessions.length > 0 && (
          <SidebarGroup>
            <SidebarGroupLabel>Recent Chats</SidebarGroupLabel>
            <SidebarGroupContent>
              <ScrollArea className="h-64">
                <div className="space-y-1">
                  {chatSessions.slice(0, 10).map((session) => (
                    <div
                      key={session.id}
                      className={cn(
                        'group flex items-center gap-2 rounded-md px-2 py-1.5 text-sm cursor-pointer transition-colors hover:bg-sidebar-accent',
                        currentSessionId === session.id && 'bg-sidebar-accent text-sidebar-accent-foreground font-medium'
                      )}
                      onClick={() => handleSessionClick(session.id)}
                    >
                      <MessageCircle className="w-3 h-3 flex-shrink-0" />
                      <span className="flex-1 truncate">{session.name || `Session ${session.id}`}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity hover-scale"
                        onClick={(e) => handleDeleteSession(session.id, e)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </SidebarGroupContent>
          </SidebarGroup>
        )}

        {/* Main Navigation */}
        <SidebarGroup>
          {!isCollapsed && <SidebarGroupLabel>Navigation</SidebarGroupLabel>}
          <SidebarGroupContent>
            <SidebarMenu>
              {mainItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    isActive={isActive(item.url)}
                    tooltip={isCollapsed ? item.title : undefined}
                  >
                    <NavLink to={item.url} end>
                      <item.icon className="w-4 h-4" />
                      {!isCollapsed && <span>{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* Settings */}
        <SidebarGroup className="mt-auto">
          {!isCollapsed && <SidebarGroupLabel>Settings</SidebarGroupLabel>}
          <SidebarGroupContent>
            <SidebarMenu>
              {settingsItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    isActive={isActive(item.url)}
                    tooltip={isCollapsed ? item.title : undefined}
                  >
                    <NavLink to={item.url}>
                      <item.icon className="w-4 h-4" />
                      {!isCollapsed && <span>{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}