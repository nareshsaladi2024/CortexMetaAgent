"""
Test script for the TokenCostAgent
"""

import os
from dotenv import load_dotenv
from agent import root_agent, check_mcp_server_health

# Load environment variables
load_dotenv()

def test_agent():
    """Test the agent with various queries"""
    
    print("TokenCostAgent - Test Suite")
    print("=" * 60)
    print()
    
    # Check server health first
    print("1. Checking MCP Server Health...")
    print("-" * 60)
    health = check_mcp_server_health()
    print(f"   Status: {health.get('status')}")
    if health.get('error_message'):
        print(f"   Error: {health.get('error_message')}")
    print()
    
    if health.get("status") != "healthy":
        print("❌ MCP server is not healthy. Please start it first:")
        print("   python server.py")
        print("   or")
        print("   .\\run-server.ps1")
        return
    
    # Test queries
    test_queries = [
        "What's the token count for: 'Hello, world!'",
        "Analyze token usage for: 'The quick brown fox jumps over the lazy dog.'",
        "How much would it cost to process this text: 'Artificial intelligence is transforming the world.'",
        "Check the token statistics for a summary request",
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
