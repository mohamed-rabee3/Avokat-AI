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
  
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  
  const isCollapsed = state === 'collapsed';
  const isActive = (path: string) => currentPath === path;

  useEffect(() => {
    // Load chat sessions
    setChatSessions(chatStore.getAllSessions());
    setCurrentSessionId(chatStore.getCurrentSessionId());
  }, []);

  const handleNewChat = () => {
    const sessionId = chatStore.createNewSession();
    setChatSessions(chatStore.getAllSessions());
    setCurrentSessionId(sessionId);
    navigate(`/chat/${sessionId}`);
    toast({
      title: "New chat created",
      description: "Started a new conversation",
    });
  };

  const handleDeleteSession = (sessionId: string, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    
    if (chatStore.deleteSession(sessionId)) {
      setChatSessions(chatStore.getAllSessions());
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
        navigate('/');
      }
      toast({
        title: "Chat deleted",
        description: "The chat session has been removed",
      });
    }
  };

  const handleSessionClick = (sessionId: string) => {
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
            className={cn(
              'w-full justify-start gap-2 hover-scale',
              isCollapsed && 'px-2 justify-center'
            )}
            variant="outline"
          >
            <Plus className="w-4 h-4" />
            {!isCollapsed && <span>New Chat</span>}
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
                      <span className="flex-1 truncate">{session.title}</span>
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