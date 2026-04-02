"""
Context Manager
Manages conversation history and state persistence
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json


@dataclass
class ConversationContext:
    """Container for conversation state"""
    conversation_id: str
    messages: List[Dict[str, str]] = field(default_factory=list)
    current_state: str = "greeting"
    topic: Optional[str] = None
    time_preference: Optional[str] = None
    selected_slot: Optional[Dict] = None
    booking_code: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    turn_count: int = 0


class ContextManager:
    """
    Manages conversation context and history
    
    Features:
    - Message history tracking
    - State persistence
    - Context expiry (30 min default)
    - Max turns enforcement (20 turns default)
    """
    
    def __init__(
        self,
        max_turns: int = 20,
        expiry_minutes: int = 30
    ):
        self.max_turns = max_turns
        self.expiry_minutes = expiry_minutes
        self.contexts: Dict[str, ConversationContext] = {}
        
    def create_context(self, conversation_id: str) -> ConversationContext:
        """Create new conversation context"""
        context = ConversationContext(conversation_id=conversation_id)
        self.contexts[conversation_id] = context
        return context
        
    def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get existing context or None if expired"""
        context = self.contexts.get(conversation_id)
        
        if not context:
            return None
            
        # Check expiry
        if self._is_expired(context):
            del self.contexts[conversation_id]
            return None
            
        return context
        
    def update_context(
        self,
        conversation_id: str,
        user_message: str,
        agent_response: str,
        state: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ConversationContext:
        """Update context with new turn"""
        context = self.get_context(conversation_id)
        
        if not context:
            context = self.create_context(conversation_id)
            
        # Add messages
        context.messages.append({"role": "user", "content": user_message})
        context.messages.append({"role": "assistant", "content": agent_response})
        
        # Update state
        if state:
            context.current_state = state
            
        # Update metadata
        if metadata:
            if "topic" in metadata:
                context.topic = metadata["topic"]
            if "time_preference" in metadata:
                context.time_preference = metadata["time_preference"]
            if "selected_slot" in metadata:
                context.selected_slot = metadata["selected_slot"]
            if "booking_code" in metadata:
                context.booking_code = metadata["booking_code"]
                
        context.turn_count += 1
        context.last_updated = datetime.utcnow()
        
        return context
        
    def get_messages_for_llm(
        self,
        conversation_id: str,
        system_prompt: str,
        max_history: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get formatted messages for LLM
        
        Returns:
            List with system prompt + recent message history
        """
        context = self.get_context(conversation_id)
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            # Get last N messages (pairs of user + assistant)
            recent = context.messages[-max_history * 2:]
            messages.extend(recent)
            
        return messages
        
    def is_max_turns_reached(self, conversation_id: str) -> bool:
        """Check if conversation has exceeded max turns"""
        context = self.get_context(conversation_id)
        if not context:
            return False
        return context.turn_count >= self.max_turns
        
    def clear_context(self, conversation_id: str) -> None:
        """Clear a conversation context"""
        if conversation_id in self.contexts:
            del self.contexts[conversation_id]
            
    def _is_expired(self, context: ConversationContext) -> bool:
        """Check if context has expired"""
        expiry = context.last_updated + timedelta(minutes=self.expiry_minutes)
        return datetime.utcnow() > expiry
        
    def cleanup_expired(self) -> int:
        """Remove expired contexts, return count removed"""
        expired_ids = [
            cid for cid, ctx in self.contexts.items()
            if self._is_expired(ctx)
        ]
        
        for cid in expired_ids:
            del self.contexts[cid]
            
        return len(expired_ids)


# Convenience function
def create_context_manager() -> ContextManager:
    """Factory function"""
    return ContextManager()
