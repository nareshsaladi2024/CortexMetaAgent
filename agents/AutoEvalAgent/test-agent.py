"""
Test script for the AutoEvalAgent
"""

import os
from dotenv import load_dotenv
from agent import auto_eval_agent, list_agents_from_inventory

# Load environment variables
load_dotenv()

def test_agent():
    """Test the agent with various queries"""
    
    print("AutoEvalAgent - Test Suite")
    print("=" * 60)
    print()
    
    # List agents
    print("1. Listing Agents from Inventory...")
    print("-" * 60)
    agents = list_agents_from_inventory()
    if agents.get("status") == "success":
        print(f"   Found {agents.get('total_count', 0)} agents")
        for agent in agents.get("agents", [])[:5]:
            print(f"   - {agent.get('id')}: {agent.get('description', 'No description')}")
    else:
        print(f"   Error: {agents.get('error_message')}")
    print()
    
    # Test queries
    test_queries = [
        "List all agents from inventory",
        "Create evaluation sets for the retriever agent",
        "Generate positive eval set for summarizer agent (1000 examples)",
        "Run regression test for retriever agent",
    ]
    
    for i, query in enumerate(test_queries, start=2):
        print(f"{i}. Test Query: {query}")
        print("-" * 60)
        try:
            response = auto_eval_agent.run(query)
            print(f"   Response: {response}")
            print()
        except Exception as e:
            print(f"   Error: {str(e)}")
            print()
    
    print("Test suite completed!")


if __name__ == "__main__":
    test_agent()

