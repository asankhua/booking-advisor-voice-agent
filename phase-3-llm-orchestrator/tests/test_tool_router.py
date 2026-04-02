"""
Tests for Tool Router
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.tool_router import create_tool_router


def test_tool_router():
    """Test tool router schemas"""
    router = create_tool_router()
    
    print("Testing Tool Router...")
    
    # Test schema generation
    print("\n1. Testing get_tool_schemas...")
    schemas = router.get_tool_schemas()
    print(f"   Generated {len(schemas)} tool schemas")
    
    expected_tools = [
        "mcp_calendar.get_availability",
        "mcp_calendar.create_hold",
        "mcp_calendar.cancel_hold",
        "mcp_calendar.reschedule_hold",
        "mcp_notes.append_pre_booking_note",
        "mcp_email.draft_advisor_email"
    ]
    
    found_tools = [s["function"]["name"] for s in schemas]
    
    for tool in expected_tools:
        if tool in found_tools:
            print(f"   ✅ {tool}")
        else:
            print(f"   ❌ {tool} (missing)")
            
    print("\n✅ Tool router schema test passed")
    
    # Note: Actual tool execution requires running MCP server
    print("\n⚠️  Tool execution tests require MCP server running on localhost:8000")
    print("   Run: cd phase-2-mcp-tools && python -m server.mcp_server")


if __name__ == "__main__":
    test_tool_router()
