"""
MCP Tool Router
Selects and executes MCP tools based on LLM requests
"""
import json
import requests
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
import os


@dataclass
class ToolResult:
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None


class ToolRouter:
    """
    Router for MCP tool execution
    
    Tools:
    - mcp_calendar: get_availability, create_hold, cancel_hold, reschedule_hold
    - mcp_notes: append_pre_booking_note
    - mcp_email: draft_advisor_email
    """
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or f"http://{os.getenv('MCP_SERVER_HOST', 'localhost')}:{os.getenv('MCP_SERVER_PORT', 8000)}"
        
    def execute(self, tool_name: str, parameters: Union[Dict[str, Any], str]) -> ToolResult:
        """
        Execute an MCP tool
        
        Args:
            tool_name: Name of tool (e.g., "mcp_calendar.get_availability")
            parameters: Tool parameters dict
            
        Returns:
            ToolResult with success status and data
        """
        try:
            if isinstance(parameters, str):
                parameters = json.loads(parameters) if parameters.strip() else {}
            # Parse tool name
            if "." in tool_name:
                module, function = tool_name.split(".", 1)
            else:
                module = tool_name
                function = None
                
            # Route to appropriate handler
            if module == "mcp_calendar":
                return self._call_calendar_tool(function, parameters)
            elif module == "mcp_notes":
                return self._call_notes_tool(function, parameters)
            elif module == "mcp_email":
                return self._call_email_tool(function, parameters)
            else:
                return ToolResult(
                    success=False,
                    data={},
                    error=f"Unknown tool: {tool_name}"
                )
                
        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=str(e)
            )
            
    def _call_calendar_tool(self, function: str, params: Dict[str, Any]) -> ToolResult:
        """Call calendar MCP tool"""
        endpoints = {
            "get_availability": "/calendar/availability",
            "create_hold": "/calendar/hold",
            "cancel_hold": "/calendar/hold/cancel",
            "reschedule_hold": "/calendar/hold/reschedule"
        }
        
        if function not in endpoints:
            return ToolResult(success=False, data={}, error=f"Unknown function: {function}")
            
        url = f"{self.base_url}{endpoints[function]}"
        
        try:
            response = requests.post(url, json=params, timeout=30)
            response.raise_for_status()
            
            return ToolResult(
                success=True,
                data=response.json()
            )
        except requests.exceptions.RequestException as e:
            return ToolResult(
                success=False,
                data={},
                error=f"Calendar API error: {str(e)}"
            )
            
    def _call_notes_tool(self, function: str, params: Dict[str, Any]) -> ToolResult:
        """Call notes MCP tool"""
        if function != "append_pre_booking_note":
            return ToolResult(success=False, data={}, error=f"Unknown function: {function}")
            
        url = f"{self.base_url}/notes/append"
        
        try:
            response = requests.post(url, json=params, timeout=30)
            response.raise_for_status()
            
            return ToolResult(
                success=True,
                data=response.json()
            )
        except requests.exceptions.RequestException as e:
            return ToolResult(
                success=False,
                data={},
                error=f"Notes API error: {str(e)}"
            )
            
    def _call_email_tool(self, function: str, params: Dict[str, Any]) -> ToolResult:
        """Call email MCP tool"""
        if function != "draft_advisor_email":
            return ToolResult(success=False, data={}, error=f"Unknown function: {function}")
            
        url = f"{self.base_url}/email/draft"
        
        try:
            response = requests.post(url, json=params, timeout=30)
            response.raise_for_status()
            
            return ToolResult(
                success=True,
                data=response.json()
            )
        except requests.exceptions.RequestException as e:
            return ToolResult(
                success=False,
                data={},
                error=f"Email API error: {str(e)}"
            )
            
    def get_tool_schemas(self) -> list:
        """Get tool schemas for LLM"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "mcp_calendar.get_availability",
                    "description": "Get available advisor slots for a date",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                            "time_preference": {"type": "string", "enum": ["morning", "afternoon", "evening"]}
                        },
                        "required": ["date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mcp_calendar.create_hold",
                    "description": "Create a tentative hold on a slot",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string"},
                            "slot_id": {"type": "string"},
                            "booking_code": {"type": "string"}
                        },
                        "required": ["topic", "slot_id", "booking_code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mcp_calendar.cancel_hold",
                    "description": "Cancel an existing hold",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "booking_code": {"type": "string"}
                        },
                        "required": ["booking_code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mcp_calendar.reschedule_hold",
                    "description": "Reschedule a hold to a new slot",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "booking_code": {"type": "string"},
                            "new_slot_id": {"type": "string"}
                        },
                        "required": ["booking_code", "new_slot_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mcp_notes.append_pre_booking_note",
                    "description": "Append a note to advisor log",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "booking_code": {"type": "string"},
                            "topic": {"type": "string"},
                            "slot_datetime": {"type": "string"},
                            "notes": {"type": "string"}
                        },
                        "required": ["booking_code", "topic", "slot_datetime"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mcp_email.draft_advisor_email",
                    "description": "Create advisor notification email draft",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "booking_code": {"type": "string"},
                            "topic": {"type": "string"},
                            "slot_datetime": {"type": "string"},
                            "additional_notes": {"type": "string"}
                        },
                        "required": ["booking_code", "topic", "slot_datetime"]
                    }
                }
            }
        ]


# Convenience function
def create_tool_router() -> ToolRouter:
    """Factory function"""
    return ToolRouter()
