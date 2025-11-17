"""
Test script for the Workflow Orchestrator
"""

import os
from dotenv import load_dotenv
from orchestrator import orchestrator_agent, check_all_agents, orchestrate_workflow, run_agents_parallel

# Load environment variables
load_dotenv()

def test_orchestrator():
    """Test the orchestrator with various queries and workflows"""
    
    print("Workflow Orchestrator - Test Suite")
    print("=" * 60)
    print()
    
    # Check all agents
    print("1. Checking All Agents...")
    print("-" * 60)
    agent_status = check_all_agents()
    for agent_name, status in agent_status["agents"].items():
        status_symbol = "✅" if status["available"] else "❌"
        print(f"   {status_symbol} {agent_name}: {'Available' if status['available'] else 'Not Available'}")
    print()
    
    all_available = agent_status["status"] == "all_available"
    
    if not all_available:
        print("⚠️  Some agents are not available. Please install them:")
        print("   cd ../agents/MetricsAgent && pip install -r requirements.txt")
        print("   cd ../agents/ReasoningCostAgent && pip install -r requirements.txt")
        print("   cd ../agents/TokenCostAgent && pip install -r requirements.txt")
        print()
    
    # Test parallel agent execution
    if all_available:
        print("2. Testing Parallel Agent Execution")
        print("-" * 60)
        try:
            agent_queries = {
                "MetricsAgent": "What are the usage statistics for the retriever agent?",
                "TokenCostAgent": "Analyze token usage for this text: 'Hello world'"
            }
            result = run_agents_parallel(agent_queries)
            print(f"   Status: {result.get('status')}")
            print(f"   Agents executed: {result.get('agents_executed')}")
            for agent, agent_result in result.get("results", {}).items():
                print(f"   ✅ {agent}: Success")
            if result.get("errors"):
                for agent, error in result["errors"].items():
                    print(f"   ❌ {agent}: {error}")
            print()
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            print()
        
        print("3. Testing Orchestrate Workflow - Comprehensive Analysis")
        print("-" * 60)
        try:
            result = orchestrate_workflow(
                "analyze_comprehensive",
                text="The quick brown fox jumps over the lazy dog.",
                agent_id="retriever"
            )
            print(f"   Status: {result.get('status')}")
            for step in result.get("steps", []):
                print(f"   Step: {step.get('step')}")
                step_result = step.get("result", {})
                if step_result.get("status") == "success":
                    print(f"      ✅ Success")
                    print(f"      Agents executed: {step_result.get('agents_executed')}")
                else:
                    print(f"      ❌ Error: {step_result.get('error_message')}")
            print()
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            print()
        
        print("4. Testing Orchestrate Workflow - Agent Performance")
        print("-" * 60)
        try:
            result = orchestrate_workflow(
                "agent_performance",
                agent_id="retriever",
                reasoning_steps=8,
                tool_calls=3,
                tokens=1189
            )
            print(f"   Status: {result.get('status')}")
            for step in result.get("steps", []):
                print(f"   Step: {step.get('step')}")
                step_result = step.get("result", {})
                if step_result.get("status") in ["success", "partial_success"]:
                    print(f"      ✅ Success")
                    print(f"      Agents executed: {step_result.get('agents_executed')}")
                else:
                    print(f"      ❌ Error")
            print()
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            print()
    
    # Test orchestrator agent queries
    test_queries = [
        "Check availability of all agents",
        "Analyze this text comprehensively: 'The quick brown fox jumps over the lazy dog'",
        "Get agent performance metrics for retriever agent with reasoning: 8 steps, 3 tool calls, 1189 tokens",
    ]
    
    for i, query in enumerate(test_queries, start=5):
        print(f"{i}. Test Query: {query}")
        print("-" * 60)
        try:
            response = orchestrator_agent.run(query)
            print(f"   Response: {response}")
            print()
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            print()
    
    print("✅ Test suite completed!")


if __name__ == "__main__":
    test_orchestrator()

