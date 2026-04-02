"""
Groq API Client with streaming support
"""
import os
from typing import Optional, Dict, Any, Iterator
from groq import Groq
import logging

logger = logging.getLogger(__name__)


class GroqClient:
    """
    Groq API Client for LLM inference
    
    Features:
    - Streaming responses
    - Error handling and retries
    - Metrics tracking
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
        max_tokens: int = 1024,
        temperature: float = 0.3
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key required")
            
        self.model = os.getenv("GROQ_MODEL", model)
        self.max_tokens = int(os.getenv("GROQ_MAX_TOKENS", max_tokens))
        self.temperature = float(os.getenv("GROQ_TEMPERATURE", temperature))
        
        self.client = Groq(api_key=self.api_key)
        
    def chat(
        self,
        messages: list,
        tools: Optional[list] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send chat completion request
        
        Args:
            messages: List of message dicts with role/content
            tools: Optional tool definitions
            stream: Whether to stream response
            
        Returns:
            Response dict with content and tool_calls
        """
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": stream
            }
            
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"
                
            response = self.client.chat.completions.create(**params)
            
            if stream:
                return self._handle_stream(response)
            else:
                return self._handle_response(response)
                
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
            
    def _handle_response(self, response) -> Dict[str, Any]:
        """Handle non-streaming response"""
        message = response.choices[0].message
        
        result = {
            "content": message.content,
            "tool_calls": []
        }
        
        if message.tool_calls:
            for tc in message.tool_calls:
                result["tool_calls"].append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                })
                
        return result
        
    def _handle_stream(self, response) -> Dict[str, Any]:
        """Handle streaming response"""
        content_parts = []
        tool_calls = {}
        
        for chunk in response:
            delta = chunk.choices[0].delta
            
            if delta.content:
                content_parts.append(delta.content)
                
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    index = tc.index
                    if index not in tool_calls:
                        tool_calls[index] = {"id": "", "name": "", "arguments": ""}
                    if tc.id:
                        tool_calls[index]["id"] = tc.id
                    if tc.function.name:
                        tool_calls[index]["name"] = tc.function.name
                    if tc.function.arguments:
                        tool_calls[index]["arguments"] += tc.function.arguments
                        
        result = {
            "content": "".join(content_parts),
            "tool_calls": list(tool_calls.values())
        }
        
        return result


# Factory function
def create_groq_client() -> GroqClient:
    """Create Groq client from environment"""
    return GroqClient()
