"""
LLM service for Gemini chat completion with multilingual support
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from google import genai
from .language_detector import LanguageDetector

logger = logging.getLogger(__name__)

class MultilingualLLMService:
    """Service for Gemini LLM interactions with multilingual support"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self.language_detector = LanguageDetector()
        
    async def initialize(self):
        """Initialize Gemini client"""
        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("LLM service initialized with Gemini")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    def _build_system_prompt(self, language: str = "english") -> str:
        """Build system prompt based on detected language"""
        
        base_prompt = """You are a professional legal assistant with expertise in legal document analysis and knowledge graph interpretation. You provide accurate, helpful, and contextually relevant responses.

IMPORTANT DISCLAIMER: This is not legal advice. All responses are for informational purposes only and should not be considered as professional legal counsel. Users should consult with qualified legal professionals for specific legal matters.

Your role is to:
1. When document context is available: Analyze the provided knowledge graph entities and relationships
2. When no document context: Provide general legal information and assistance based on your training
3. Answer questions about legal concepts, procedures, and general legal topics
4. Provide clear, accurate explanations of legal concepts
5. Maintain professional and helpful communication

Guidelines:
- If document context is provided, prioritize information from the knowledge graph
- If no document context is available, use your general legal knowledge
- Always clearly state when you're providing general information vs. document-specific information
- Be precise and avoid speculation
- Maintain a professional tone throughout
- You can have general conversations and answer questions even without uploaded documents"""
        
        if language == "arabic":
            arabic_enhancement = """

تعزيزات خاصة للمحتوى العربي:
- استخدم المصطلحات القانونية العربية المناسبة
- اعترف بالسياق الثقافي والقانوني العربي
- قدم التفسيرات باللغة العربية عندما يكون ذلك مناسباً
- استخدم المصطلحات القانونية الإسلامية عند الاقتضاء
- اعترف بالاختلافات في الأنظمة القانونية العربية"""
            return base_prompt + arabic_enhancement
        
        return base_prompt
    
    def _build_context_prompt(self, retrieval_result: Dict[str, Any]) -> str:
        """Build enhanced context prompt from retrieval results"""
        
        context_parts = []
        
        # Add entities context
        if retrieval_result.get("entities"):
            context_parts.append("=== ENTITIES FROM DOCUMENTS ===")
            for entity in retrieval_result["entities"]:
                entity_info = f"- {entity['name']} ({entity['entity_type']})"
                if entity.get("description"):
                    entity_info += f": {entity['description']}"
                if entity.get("language"):
                    entity_info += f" [Language: {entity['language']}]"
                if entity.get("relevance_score"):
                    entity_info += f" [Relevance: {entity['relevance_score']}]"
                context_parts.append(entity_info)
        
        # Add relationships context
        if retrieval_result.get("relationships"):
            context_parts.append("\n=== RELATIONSHIPS ===")
            for rel in retrieval_result["relationships"]:
                rel_info = f"- {rel['type']}"
                if rel.get("language"):
                    rel_info += f" [Language: {rel['language']}]"
                context_parts.append(rel_info)
        
        # Add expanded context (related entities and relationships)
        if retrieval_result.get("expanded_context"):
            context_parts.append("\n=== RELATED INFORMATION ===")
            for item in retrieval_result["expanded_context"]:
                if item["type"] == "expanded_entity":
                    entity = item["entity"]
                    rel_info = f"- Related: {entity['name']} ({entity['entity_type']})"
                    if item.get("relationship_type"):
                        rel_info += f" via {item['relationship_type']}"
                    context_parts.append(rel_info)
                elif item["type"] == "expanded_relationship":
                    rel = item["relationship"]
                    rel_info = f"- Relationship: {rel['type']}"
                    if item.get("relationship_type"):
                        rel_info += f" ({item['relationship_type']})"
                    context_parts.append(rel_info)
        
        # Add context chunks (document content)
        if retrieval_result.get("context_chunks"):
            context_parts.append("\n=== DOCUMENT CONTENT ===")
            for i, chunk in enumerate(retrieval_result["context_chunks"]):
                context_parts.append(f"Chunk {i+1}: {chunk}")
        
        # Add search terms used for transparency
        if retrieval_result.get("search_terms"):
            context_parts.append(f"\n=== SEARCH TERMS USED ===")
            context_parts.append(f"Terms: {', '.join(retrieval_result['search_terms'])}")
        
        return "\n".join(context_parts)
    
    def _build_chat_history_prompt(self, messages: List[Dict[str, Any]], max_tokens: int = 1000) -> str:
        """Build chat history prompt with token limit"""
        
        history_parts = []
        current_tokens = 0
        
        # Process messages in reverse order (most recent first)
        for message in reversed(messages):
            role = message.get("role", "user")
            content = message.get("content", "")
            
            # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
            message_tokens = len(content) // 4
            
            if current_tokens + message_tokens > max_tokens:
                break
            
            if role == "user":
                history_parts.insert(0, f"User: {content}")
            elif role == "assistant":
                history_parts.insert(0, f"Assistant: {content}")
            
            current_tokens += message_tokens
        
        if history_parts:
            return "=== RECENT CHAT HISTORY ===\n" + "\n".join(history_parts)
        
        return ""
    
    async def generate_response(
        self,
        user_message: str,
        retrieval_result: Dict[str, Any],
        chat_history: List[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Generate response using Gemini with multilingual support
        
        Args:
            user_message: User's question
            retrieval_result: Retrieved knowledge graph context
            chat_history: Previous chat messages
            stream: Whether to stream the response
            
        Yields:
            Response chunks as they are generated
        """
        
        if not self.client:
            raise RuntimeError("LLM service not initialized")
        
        try:
            # Detect language of user message
            detected_language = self.language_detector.detect_language(user_message)
            
            # Build prompts
            system_prompt = self._build_system_prompt(detected_language)
            context_prompt = self._build_context_prompt(retrieval_result)
            history_prompt = self._build_chat_history_prompt(chat_history or [])
            
            # Combine all prompts
            full_prompt = f"{system_prompt}\n\n{context_prompt}\n\n{history_prompt}\n\nUser Question: {user_message}\n\nAssistant Response:"
            
            logger.info(f"Generating response for language: {detected_language}")
            
            if stream:
                # Stream response
                async for chunk in await self.client.aio.models.generate_content_stream(
                    model="gemini-1.5-flash",
                    contents=full_prompt
                ):
                    if chunk.text:
                        yield chunk.text
            else:
                # Non-streaming response
                response = await self.client.aio.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=full_prompt
                )
                yield response.text
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            yield f"I apologize, but I encountered an error while processing your request: {str(e)}"
    
    async def generate_response_sync(
        self,
        user_message: str,
        retrieval_result: Dict[str, Any],
        chat_history: List[Dict[str, Any]] = None
    ) -> str:
        """
        Generate response synchronously (non-streaming)
        
        Args:
            user_message: User's question
            retrieval_result: Retrieved knowledge graph context
            chat_history: Previous chat messages
            
        Returns:
            Complete response text
        """
        
        response_text = ""
        async for chunk in self.generate_response(user_message, retrieval_result, chat_history, stream=False):
            response_text += chunk
        
        return response_text
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        return len(text) // 4
    
    async def validate_api_key(self) -> bool:
        """Validate Gemini API key"""
        try:
            if not self.client:
                return False
            
            # Try a simple test request
            response = await self.client.aio.models.generate_content(
                model="gemini-1.5-flash",
                contents="Hello"
            )
            return bool(response.text)
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False

# Global instance (will be initialized with API key)
llm_service: Optional[MultilingualLLMService] = None

async def initialize_llm_service(api_key: str) -> MultilingualLLMService:
    """Initialize global LLM service"""
    global llm_service
    llm_service = MultilingualLLMService(api_key)
    await llm_service.initialize()
    return llm_service

def get_llm_service() -> MultilingualLLMService:
    """Get global LLM service instance"""
    if llm_service is None:
        raise RuntimeError("LLM service not initialized")
    return llm_service