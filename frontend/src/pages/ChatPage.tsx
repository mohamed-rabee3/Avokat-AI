import { useParams } from 'react-router-dom';
import { ChatInterface } from "@/components/ChatInterface";

const ChatPage = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  
  return (
    <div className="h-full">
      <ChatInterface sessionId={sessionId} />
    </div>
  );
};

export default ChatPage;