import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ChatInterface } from "@/components/ChatInterface";
import { apiService } from "@/lib/api";

const Index = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect to a new chat session
    const createNewSession = async () => {
      try {
        const session = await apiService.createSession('New Chat');
        navigate(`/chat/${session.id}`, { replace: true });
      } catch (error) {
        console.error('Failed to create session:', error);
        // If creation fails, show the interface anyway
      }
    };

    createNewSession();
  }, [navigate]);

  return (
    <div className="h-full">
      <ChatInterface />
    </div>
  );
};

export default Index;
