"""
Response Formatter
Formats LLM responses for TTS with phonetic codes
"""
import re
from typing import Optional


class ResponseFormatter:
    """
    Formats responses for TTS optimization
    
    Features:
    - Phonetic code formatting (KY-1234 → "K as in Kilo...")
    - Timezone confirmation
    - Pause markers for TTS
    """
    
    # Phonetic alphabet
    PHONETIC = {
        'A': 'Alpha', 'B': 'Bravo', 'C': 'Charlie', 'D': 'Delta', 'E': 'Echo',
        'F': 'Foxtrot', 'G': 'Golf', 'H': 'Hotel', 'I': 'India', 'J': 'Juliet',
        'K': 'Kilo', 'L': 'Lima', 'M': 'Mike', 'N': 'November', 'O': 'Oscar',
        'P': 'Papa', 'Q': 'Quebec', 'R': 'Romeo', 'S': 'Sierra', 'T': 'Tango',
        'U': 'Uniform', 'V': 'Victor', 'W': 'Whiskey', 'X': 'X-ray', 'Y': 'Yankee',
        'Z': 'Zulu', '0': 'Zero', '1': 'One', '2': 'Two', '3': 'Three',
        '4': 'Four', '5': 'Five', '6': 'Six', '7': 'Seven', '8': 'Eight', '9': 'Nine'
    }
    
    def format_booking_code(self, code: str) -> str:
        """
        Convert booking code to phonetic format
        
        Example: KY-1234 → "K as in Kilo, Y as in Yankee, dash, 1, 2, 3, 4"
        """
        parts = []
        
        for char in code.upper():
            if char == '-':
                parts.append("dash")
            elif char in self.PHONETIC:
                letter = self.PHONETIC[char]
                if char.isalpha():
                    parts.append(f"{char} as in {letter}")
                else:
                    parts.append(letter.lower())
                    
        return ", ".join(parts)
        
    def format_with_timezone(self, datetime_str: str) -> str:
        """
        Format datetime with IST timezone confirmation
        
        Example: 2026-04-15T10:00:00+05:30 → "Tuesday at 10 AM IST"
        """
        from datetime import datetime
        
        try:
            dt = datetime.fromisoformat(datetime_str)
            
            # Get day name
            day_name = dt.strftime("%A")
            
            # Format time
            hour = dt.hour
            minute = dt.minute
            
            if minute == 0:
                time_str = f"{hour} AM" if hour < 12 else f"{hour - 12} PM"
            else:
                time_str = f"{hour}:{minute:02d} AM" if hour < 12 else f"{hour - 12}:{minute:02d} PM"
                
            if hour == 12:
                time_str = "12 PM"
            elif hour == 0:
                time_str = "12 AM"
                
            return f"{day_name} at {time_str} IST"
            
        except:
            return datetime_str
            
    def format_for_tts(self, text: str, booking_code: Optional[str] = None, slot_datetime: Optional[str] = None) -> str:
        """
        Format response for optimal TTS
        
        Args:
            text: Original text
            booking_code: Optional code to phoneticize
            slot_datetime: Optional datetime to format
        """
        formatted = text
        
        # Replace booking code with phonetic version
        if booking_code and booking_code in text:
            phonetic_code = self.format_booking_code(booking_code)
            formatted = formatted.replace(booking_code, phonetic_code)
            
        # Add timezone confirmation if datetime present
        if slot_datetime and "IST" not in formatted:
            time_str = self.format_with_timezone(slot_datetime)
            if "confirmed" in formatted.lower():
                # Insert timezone info
                formatted = formatted.replace(".", f" for {time_str}.", 1)
                
        # Add pause markers for better TTS flow
        formatted = self._add_pause_markers(formatted)
        
        return formatted
        
    def _add_pause_markers(self, text: str) -> str:
        """Add subtle pause markers for TTS"""
        # Add comma after transition words
        transitions = ["Hello", "Thank you", "Your slot", "Perfect", "I understand"]
        
        for trans in transitions:
            text = text.replace(f"{trans} ", f"{trans}, ")
            
        # Ensure pause before code reading
        text = re.sub(r'(booking code is|code is)\s+([A-Z])', r'\1, \2', text, flags=re.IGNORECASE)
        
        return text
        
    def generate_secure_url_message(self, booking_code: str) -> str:
        """Generate message about secure URL"""
        return f"Please complete your registration by providing contact details at the secure link shown on screen. Your booking code is {booking_code}."


# Convenience function
def create_response_formatter() -> ResponseFormatter:
    """Factory function"""
    return ResponseFormatter()
