"""
Tests for MCP Server (FastAPI)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from server.mcp_server import app


client = TestClient(app)


def test_health():
    """Test health endpoint"""
    print("Testing /health...")
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("   ✅ Health check passed")


def test_calendar_availability():
    """Test calendar availability endpoint"""
    print("\nTesting /calendar/availability...")
    from datetime import datetime
    
    today = datetime.now().strftime("%Y-%m-%d")
    response = client.post(
        "/calendar/availability",
        json={"date": today, "time_preference": "morning"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "slots" in data
    print(f"   ✅ Found {len(data['slots'])} slots")


def run_all_tests():
    """Run all MCP server tests"""
    print("=" * 50)
    print("MCP Server Tests")
    print("=" * 50)
    
    try:
        test_health()
        test_calendar_availability()
        print("\n✅ All MCP server tests passed")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
