"""
Test script for the ActionExtractor Agent
"""

import os
from dotenv import load_dotenv
from agent import root_agent, check_reasoning_cost_health

# Load environment variables
load_dotenv()

def test_agent():
    """Test the agent with various queries"""
    
    print("ActionExtractor Agent - Test Suite")
    print("=" * 60)
    print()
    
    # Check server health first
    print("1. Checking ReasoningCost MCP Server Health...")
    print("-" * 60)
    health = check_reasoning_cost_health()
    print(f"   Status: {health.get('status')}")
    if health.get('error_message'):
        print(f"   Error: {health.get('error_message')}")
    print()
    
    if health.get("status") != "healthy":
        print("❌ ReasoningCost MCP server is not healthy. Please start it first:")
        print("   cd ../../mcp-servers/mcp-reasoning-cost")
        print("   python server.py")
        print("   or")
        print("   .\\run-server.ps1")
        return
    
    # Test queries
    test_queries = [
        "Validate this reasoning chain: 8 steps, 3 tool calls, 1189 tokens. Extract the key actions.",
        "Is this reasoning chain cost-efficient? Steps: 5, Tool calls: 1, Tokens: 650",
        "Extract actions from a reasoning process with 12 steps, 5 tool calls, and 2400 tokens",
        "Check if this reasoning chain is too expensive: Steps: 15, Tool calls: 8, Tokens: 3500",
    ]
    
    for i, query in enumerate(test_queries, start=2):
        print(f"{i}. Test Query: {query}")
        print("-" * 60)
        try:
            response = root_agent.run(query)
            print(f"   Response: {response}")
            print()
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            print()
    
    print("✅ Test suite completed!")


if __name__ == "__main__":
    test_agent()

