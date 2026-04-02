"""
State Machine for Voice Agent
4-state progression: Greeting → Intent → Time → Confirm
"""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class State(Enum):
    GREETING = "greeting"
    INTENT_CLASSIFICATION = "intent_classification" 
    TIME_PREFERENCE = "time_preference"
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"


class StateMachine:
    """
    Strict 4-state state machine for booking flow
    
    States:
    1. GREETING - Must deliver disclaimer first
    2. INTENT_CLASSIFICATION - Identify topic
    3. TIME_PREFERENCE - Get time preference, offer slots
    4. CONFIRMATION - Confirm booking details
    5. COMPLETED - Booking done
    """
    
    # Valid transitions
    TRANSITIONS = {
        State.GREETING: [State.INTENT_CLASSIFICATION],
        State.INTENT_CLASSIFICATION: [State.TIME_PREFERENCE],
        State.TIME_PREFERENCE: [State.CONFIRMATION],
        State.CONFIRMATION: [State.COMPLETED],
        State.COMPLETED: []
    }
    
    def __init__(self):
        self.current_state = State.GREETING
        self.context = {
            "topic": None,
            "time_preference": None,
            "selected_slot": None,
            "booking_code": None,
            "conversation_history": [],
            "disclaimer_delivered": False,
            "turn_count": 0
        }
        
    def transition(self, new_state: State, data: Dict[str, Any] = None) -> bool:
        """
        Attempt state transition
        
        Returns:
            True if transition valid, False otherwise
        """
        if new_state not in self.TRANSITIONS[self.current_state]:
            return False
            
        self.current_state = new_state
        
        # Update context with transition data
        if data:
            self.context.update(data)
            
        self.context["turn_count"] += 1
        return True
        
    def can_transition_to(self, state: State) -> bool:
        """Check if transition to state is valid"""
        return state in self.TRANSITIONS[self.current_state]
        
    def get_required_actions(self) -> list:
        """Get actions required in current state"""
        actions = []
        
        if self.current_state == State.GREETING:
            if not self.context["disclaimer_delivered"]:
                actions.append("DELIVER_DISCLAIMER")
            actions.append("CLASSIFY_INTENT")
            
        elif self.current_state == State.INTENT_CLASSIFICATION:
            if not self.context["topic"]:
                actions.append("CONFIRM_TOPIC")
            actions.append("GET_TIME_PREFERENCE")
            
        elif self.current_state == State.TIME_PREFERENCE:
            if not self.context["selected_slot"]:
                actions.append("OFFER_SLOTS")
            actions.append("CONFIRM_BOOKING")
            
        elif self.current_state == State.CONFIRMATION:
            actions.append("EXECUTE_BOOKING")
            actions.append("PROVIDE_CODE")
            
        return actions
        
    def to_dict(self) -> Dict[str, Any]:
        """Serialize state machine"""
        return {
            "current_state": self.current_state.value,
            "context": self.context
        }
        
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Deserialize state machine"""
        self.current_state = State(data["current_state"])
        self.context = data["context"]


# State requirements for compliance
STATE_REQUIREMENTS = {
    State.GREETING: {
        "must_say_disclaimer": True,
        "can_collect_pii": False,
        "can_give_advice": False
    },
    State.INTENT_CLASSIFICATION: {
        "must_say_disclaimer": False,
        "can_collect_pii": False,
        "can_give_advice": False
    },
    State.TIME_PREFERENCE: {
        "must_say_disclaimer": False,
        "can_collect_pii": False,
        "can_give_advice": False
    },
    State.CONFIRMATION: {
        "must_say_disclaimer": False,
        "can_collect_pii": False,
        "can_give_advice": False
    }
}
