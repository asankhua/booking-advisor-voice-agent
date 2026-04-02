"""
Main LLM Orchestrator
Wires all components together for end-to-end processing
"""
import json
import os
from typing import Optional, Dict, Any, Tuple, List
import logging

from core.groq_client import create_groq_client
from core.state_machine import StateMachine, State, STATE_REQUIREMENTS
from core.context_manager import create_context_manager
from nlu.intent_classifier import create_intent_classifier, Intent
from nlu.topic_router import create_topic_router
from tools.tool_router import create_tool_router
from formatters.response_formatter import create_response_formatter

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """
    Main orchestrator for voice agent
    
    Pipeline:
    1. Receive user text
    2. Check compliance (PII, advice)
    3. Classify intent & route topic
    4. Update state machine
    5. Call LLM with context
    6. Execute any tool calls
    7. Format response for TTS
    """
    
    def __init__(self, system_prompt_path: Optional[str] = None):
        # Initialize components
        self.groq = create_groq_client()
        self.intent_classifier = create_intent_classifier()
        self.topic_router = create_topic_router()
        self.tool_router = create_tool_router()
        self.formatter = create_response_formatter()
        self.context_manager = create_context_manager()
        
        # State machines per conversation
        self.state_machines: Dict[str, StateMachine] = {}
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt(system_prompt_path)
        
    def _load_system_prompt(self, path: Optional[str]) -> str:
        """Load system prompt from file"""
        if not path:
            path = os.path.join(
                os.path.dirname(__file__),
                "../prompts/system_prompt.txt"
            )
            
        try:
            with open(path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"System prompt not found at {path}, using default")
            return "You are a helpful voice assistant."
            
    def process(self, conversation_id: str, user_text: str) -> Dict[str, Any]:
        """
        Process user input through the full pipeline
        
        Returns:
            Dict with response_text, audio_ready_text, state, and metadata
        """
        # Get or create state machine
        if conversation_id not in self.state_machines:
            self.state_machines[conversation_id] = StateMachine()
            
        state_machine = self.state_machines[conversation_id]
        
        # Step 1: Compliance checks
        compliance_result = self._check_compliance(user_text)
        if compliance_result["should_interrupt"]:
            return {
                "response_text": compliance_result["message"],
                "audio_ready_text": compliance_result["message"],
                "state": state_machine.current_state.value,
                "compliance_triggered": True,
                "intent": "blocked"
            }
            
        # Step 2: Classify intent
        intent_result = self.intent_classifier.classify(user_text)
        
        # Handle investment advice
        if intent_result.requires_advice_warning:
            advice_response = (
                "I cannot provide investment advice or product recommendations. "
                "For general investor education you can refer to official SEBI investor resources online. "
                "I'm only here to help you book an appointment with a human advisor. Would you like to continue?"
            )
            return {
                "response_text": advice_response,
                "audio_ready_text": advice_response,
                "state": state_machine.current_state.value,
                "compliance_triggered": True,
                "intent": "investment_advice"
            }
            
        # Step 3: Route topic (if intent involves booking)
        topic_result = None
        if intent_result.intent in [Intent.BOOK_NEW, Intent.RESCHEDULE, Intent.CANCEL]:
            topic_result = self.topic_router.route(user_text)
            if topic_result.topic.value != "Unknown":
                state_machine.context["topic"] = topic_result.topic.value
                
        # Step 4: Handle state transitions based on intent
        self._handle_state_transition(state_machine, intent_result, user_text)
        
        # Step 5: Build LLM messages
        messages = self._build_messages(conversation_id, user_text, state_machine)
        
        # Step 6: Call LLM
        llm_response = self.groq.chat(
            messages=messages,
            tools=self.tool_router.get_tool_schemas()
        )
        
        # Step 7: Execute tool calls
        tool_results = []
        if llm_response.get("tool_calls"):
            for tc in llm_response["tool_calls"]:
                result = self.tool_router.execute(tc["name"], tc["arguments"])
                tool_results.append(result)
                
                # Update state based on tool result
                if result.success:
                    self._update_state_from_tool(state_machine, tc["name"], result.data)
            # Milestone: calendar hold must be followed by notes + email (if LLM omitted them)
            self._ensure_notes_and_email_after_hold(llm_response["tool_calls"], tool_results)
                    
        # Step 8: Get final response text
        response_text = llm_response.get("content", "")
        
        # Step 9: Format for TTS
        audio_text = self.formatter.format_for_tts(
            response_text,
            booking_code=state_machine.context.get("booking_code"),
            slot_datetime=state_machine.context.get("selected_slot", {}).get("datetime") if state_machine.context.get("selected_slot") else None
        )
        
        # Step 10: Update context
        self.context_manager.update_context(
            conversation_id,
            user_text,
            response_text,
            state=state_machine.current_state.value,
            metadata={
                "topic": state_machine.context.get("topic"),
                "booking_code": state_machine.context.get("booking_code"),
                "selected_slot": state_machine.context.get("selected_slot")
            }
        )
        
        return {
            "response_text": response_text,
            "audio_ready_text": audio_text,
            "state": state_machine.current_state.value,
            "intent": intent_result.intent.value,
            "topic": topic_result.topic.value if topic_result else None,
            "compliance_triggered": False,
            "tool_calls": len(tool_results),
            "booking_code": state_machine.context.get("booking_code")
        }
        
    def _check_compliance(self, text: str) -> Dict[str, Any]:
        """Check for PII and other compliance issues"""
        import re
        
        # PII patterns
        patterns = {
            "phone": r'\b(\+91[\s-]?)?[6-9]\d{9}\b',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "pan": r'\b[A-Z]{5}[0-9]{4}[A-Z]\b',
            "aadhaar": r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            "account": r'\b\d{9,16}\b'
        }
        
        for pii_type, pattern in patterns.items():
            if re.search(pattern, text):
                return {
                    "should_interrupt": True,
                    "message": "For your security, please don't share personal details like phone numbers or account information on this call. You can provide those securely after receiving your booking confirmation.",
                    "pii_type": pii_type
                }
                
        return {"should_interrupt": False}
        
    def _handle_state_transition(self, state_machine: StateMachine, intent_result, user_text: str):
        """Handle state machine transitions based on intent"""
        current = state_machine.current_state
        
        # State 1 → 2: After greeting, move to intent classification
        if current == State.GREETING:
            if intent_result.intent != Intent.UNKNOWN:
                state_machine.transition(State.INTENT_CLASSIFICATION)
                state_machine.context["disclaimer_delivered"] = True
                
        # State 2 → 3: After topic confirmed, move to time preference
        elif current == State.INTENT_CLASSIFICATION:
            if state_machine.context.get("topic"):
                state_machine.transition(State.TIME_PREFERENCE)
                
        # State 3 → 4: After slot selected, move to confirmation
        elif current == State.TIME_PREFERENCE:
            # Check if user selected a slot (would be detected by LLM tool call)
            pass  # Transition happens after tool execution
            
    def _build_messages(self, conversation_id: str, user_text: str, state_machine: StateMachine) -> list:
        """Build message list for LLM"""
        # Get history
        messages = self.context_manager.get_messages_for_llm(
            conversation_id,
            self.system_prompt
        )
        
        # Add current state info to context
        state_info = f"\n[Current State: {state_machine.current_state.value}]"
        state_info += f"\n[Topic: {state_machine.context.get('topic', 'Unknown')}]"
        
        if messages[0]["role"] == "system":
            messages[0]["content"] += state_info
            
        # Add user message if not already in history
        if not messages or messages[-1].get("content") != user_text:
            messages.append({"role": "user", "content": user_text})
            
        return messages
        
    def _ensure_notes_and_email_after_hold(
        self, tool_calls: List[Dict[str, Any]], tool_results: List[Any]
    ) -> None:
        """ARCHITECTURE: on confirm, MCP calendar + notes + email. Backfill if model only called create_hold."""
        names = {tc.get("name") for tc in tool_calls}
        for tc, tr in zip(tool_calls, tool_results):
            if tc.get("name") != "mcp_calendar.create_hold" or not tr.success:
                continue
            data = tr.data or {}
            if not data.get("success"):
                continue
            raw = tc.get("arguments")
            try:
                args = json.loads(raw) if isinstance(raw, str) else (raw or {})
            except json.JSONDecodeError:
                args = {}
            topic = args.get("topic")
            booking_code = args.get("booking_code")
            slot_dt = data.get("slot_datetime") or ""
            if not topic or not booking_code:
                continue
            if "mcp_notes.append_pre_booking_note" not in names:
                r = self.tool_router.execute(
                    "mcp_notes.append_pre_booking_note",
                    {
                        "booking_code": booking_code,
                        "topic": topic,
                        "slot_datetime": slot_dt,
                        "notes": "Voice agent booking (orchestrator sync)",
                    },
                )
                if r.success:
                    logger.info("Synced MCP notes after create_hold")
            if "mcp_email.draft_advisor_email" not in names:
                r = self.tool_router.execute(
                    "mcp_email.draft_advisor_email",
                    {
                        "booking_code": booking_code,
                        "topic": topic,
                        "slot_datetime": slot_dt,
                        "additional_notes": "",
                    },
                )
                if r.success:
                    logger.info("Synced MCP email draft after create_hold")

    def _update_state_from_tool(self, state_machine: StateMachine, tool_name: str, result: Dict):
        """Update state based on tool execution result"""
        if tool_name == "mcp_calendar.create_hold" and result.get("success"):
            # Move to confirmation state after successful hold
            if state_machine.current_state == State.TIME_PREFERENCE:
                state_machine.transition(State.CONFIRMATION)
                
            # Extract booking code from result
            hold_id = result.get("hold_id", "")
            if hold_id:
                state_machine.context["booking_code"] = hold_id
                
        elif tool_name == "mcp_calendar.get_availability" and result.get("slots"):
            # Store available slots in context
            state_machine.context["available_slots"] = result.get("slots")


# Convenience function
def create_orchestrator() -> LLMOrchestrator:
    """Factory function"""
    return LLMOrchestrator()
