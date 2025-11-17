"""
Test script for the MetricsAgent
"""

import os
from dotenv import load_dotenv
from agent import root_agent, check_agent_inventory_health

# Load environment variables
load_dotenv()

def test_agent():
    """Test the agent with various queries"""
    
    print("MetricsAgent - Test Suite")
    print("=" * 60)
    print()
    
    # Check server health first
    print("1. Checking AgentInventory MCP Server Health...")
    print("-" * 60)
    health = check_agent_inventory_health()
    print(f"   Status: {health.get('status')}")
    if health.get('error_message'):
        print(f"   Error: {health.get('error_message')}")
    print()
    
    if health.get("status") != "healthy":
        print("❌ AgentInventory MCP server is not healthy. Please start it first:")
        print("   cd ../../mcp-servers/mcp-agent-inventory")
        print("   python server.py")
        print("   or")
        print("   .\\run-server.ps1")
        return
    
    # Test queries
    test_queries = [
        "What are the usage statistics for the retriever agent?",
        "Get usage statistics for the retriever agent",
        "How many times has the retriever agent been executed?",
        "What is the failure rate for the retriever agent?",
        "List all available agents in the inventory",
        "What are the latency metrics for the retriever agent?",
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
