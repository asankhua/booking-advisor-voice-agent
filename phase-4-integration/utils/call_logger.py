"""
Call Logging System for Voice Agent
Logs all voice interactions, bookings, and system events
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class CallLogEntry:
    """Single call/interaction log entry"""
    timestamp: str
    conversation_id: str
    event_type: str  # voice_input, voice_output, booking_created, error, etc.
    state: str
    transcript: Optional[str] = None
    response: Optional[str] = None
    booking_code: Optional[str] = None
    topic: Optional[str] = None
    slot_datetime: Optional[str] = None
    duration_ms: Optional[int] = None
    latency_ms: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CallLogger:
    """
    Central logging system for voice agent
    
    Logs:
    - Voice inputs (transcripts)
    - Voice outputs (responses)
    - Booking creations
    - MCP tool calls
    - Errors and exceptions
    - Latency metrics
    """
    
    def __init__(self, log_dir: str = None):
        # Use root logs folder by default
        if log_dir is None:
            # Go up to project root and use logs folder
            log_dir = Path(__file__).parent.parent.parent / "logs"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Daily log files
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"calls_{self.current_date}.jsonl"
        
        # Summary stats file
        self.stats_file = self.log_dir / "call_stats.json"
        
    def _get_timestamp(self) -> str:
        """Get ISO timestamp"""
        return datetime.utcnow().isoformat() + "Z"
        
    def _rotate_file_if_needed(self):
        """Rotate log file if date changed"""
        current = datetime.now().strftime("%Y-%m-%d")
        if current != self.current_date:
            self.current_date = current
            self.log_file = self.log_dir / f"calls_{self.current_date}.jsonl"
            
    def log_voice_input(
        self,
        conversation_id: str,
        transcript: str,
        state: str,
        audio_duration_ms: Optional[int] = None,
        metadata: Optional[Dict] = None
    ):
        """Log user voice input"""
        self._rotate_file_if_needed()
        
        entry = CallLogEntry(
            timestamp=self._get_timestamp(),
            conversation_id=conversation_id,
            event_type="voice_input",
            state=state,
            transcript=transcript,
            duration_ms=audio_duration_ms,
            metadata=metadata
        )
        
        self._write_entry(entry)
        
    def log_voice_output(
        self,
        conversation_id: str,
        response: str,
        state: str,
        tts_latency_ms: Optional[int] = None,
        metadata: Optional[Dict] = None
    ):
        """Log agent voice output"""
        self._rotate_file_if_needed()
        
        entry = CallLogEntry(
            timestamp=self._get_timestamp(),
            conversation_id=conversation_id,
            event_type="voice_output",
            state=state,
            response=response,
            latency_ms=tts_latency_ms,
            metadata=metadata
        )
        
        self._write_entry(entry)
        
    def log_booking_created(
        self,
        conversation_id: str,
        booking_code: str,
        topic: str,
        slot_datetime: str,
        metadata: Optional[Dict] = None
    ):
        """Log successful booking creation"""
        self._rotate_file_if_needed()
        
        entry = CallLogEntry(
            timestamp=self._get_timestamp(),
            conversation_id=conversation_id,
            event_type="booking_created",
            state="completed",
            booking_code=booking_code,
            topic=topic,
            slot_datetime=slot_datetime,
            metadata=metadata
        )
        
        self._write_entry(entry)
        self._update_stats("bookings_created", 1)
        
    def log_mcp_call(
        self,
        conversation_id: str,
        tool_name: str,
        success: bool,
        latency_ms: int,
        error: Optional[str] = None
    ):
        """Log MCP tool call"""
        self._rotate_file_if_needed()
        
        entry = CallLogEntry(
            timestamp=self._get_timestamp(),
            conversation_id=conversation_id,
            event_type="mcp_call",
            state="",
            response=f"{tool_name}: {'success' if success else 'failed'}",
            latency_ms=latency_ms,
            error_message=error,
            metadata={"tool": tool_name, "success": success}
        )
        
        self._write_entry(entry)
        
    def log_error(
        self,
        conversation_id: str,
        error_message: str,
        state: str,
        exception: Optional[str] = None
    ):
        """Log error/exception"""
        self._rotate_file_if_needed()
        
        entry = CallLogEntry(
            timestamp=self._get_timestamp(),
            conversation_id=conversation_id,
            event_type="error",
            state=state,
            error_message=error_message,
            metadata={"exception": exception} if exception else None
        )
        
        self._write_entry(entry)
        self._update_stats("errors", 1)
        
    def log_conversation_start(self, conversation_id: str):
        """Log new conversation start"""
        self._rotate_file_if_needed()
        
        entry = CallLogEntry(
            timestamp=self._get_timestamp(),
            conversation_id=conversation_id,
            event_type="conversation_start",
            state="greeting"
        )
        
        self._write_entry(entry)
        self._update_stats("conversations", 1)
        
    def log_conversation_end(
        self,
        conversation_id: str,
        final_state: str,
        total_turns: int
    ):
        """Log conversation end"""
        self._rotate_file_if_needed()
        
        entry = CallLogEntry(
            timestamp=self._get_timestamp(),
            conversation_id=conversation_id,
            event_type="conversation_end",
            state=final_state,
            metadata={"total_turns": total_turns}
        )
        
        self._write_entry(entry)
        
    def _write_entry(self, entry: CallLogEntry):
        """Write entry to log file"""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(asdict(entry), default=str) + '\n')
            
    def _update_stats(self, metric: str, increment: int = 1):
        """Update summary statistics"""
        stats = {}
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                stats = json.load(f)
                
        stats[metric] = stats.get(metric, 0) + increment
        stats["last_updated"] = self._get_timestamp()
        
        with open(self.stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
            
    def get_logs(
        self,
        conversation_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """Query logs with filters"""
        logs = []
        
        # Read all log files
        for log_file in self.log_dir.glob("calls_*.jsonl"):
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Apply filters
                        if conversation_id and entry.get("conversation_id") != conversation_id:
                            continue
                        if event_type and entry.get("event_type") != event_type:
                            continue
                        if start_time and entry.get("timestamp", "") < start_time:
                            continue
                        if end_time and entry.get("timestamp", "") > end_time:
                            continue
                            
                        logs.append(entry)
                    except json.JSONDecodeError:
                        continue
                        
        # Sort by timestamp and limit
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return logs[:limit]
        
    def get_conversation_history(self, conversation_id: str) -> list:
        """Get full conversation history"""
        return self.get_logs(conversation_id=conversation_id, limit=1000)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get summary statistics"""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                return json.load(f)
        return {}
        
    def export_to_csv(self, output_file: str):
        """Export logs to CSV format"""
        import csv
        
        logs = self.get_logs(limit=10000)
        
        if not logs:
            return
            
        # Get all possible fields
        fields = set()
        for log in logs:
            fields.update(log.keys())
        fields = sorted(fields)
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(logs)


# Convenience function
def create_call_logger(log_dir: str = "logs") -> CallLogger:
    """Factory function"""
    return CallLogger(log_dir)


# Example usage
if __name__ == "__main__":
    # Demo usage
    logger = create_call_logger()
    
    # Simulate a conversation
    conv_id = "test-conv-123"
    
    logger.log_conversation_start(conv_id)
    logger.log_voice_input(conv_id, "I want to book an appointment", "greeting", 2500)
    logger.log_voice_output(conv_id, "Hello! I cannot provide investment advice. What topic?", "intent", 800)
    logger.log_booking_created(conv_id, "KY-1234", "KYC/Onboarding", "2026-04-15T10:00:00+05:30")
    logger.log_conversation_end(conv_id, "completed", 4)
    
    # Query logs
    print("All logs:")
    for log in logger.get_logs(limit=5):
        print(f"  {log['timestamp']} | {log['event_type']} | {log.get('booking_code', 'N/A')}")
        
    print("\nStats:", logger.get_stats())
