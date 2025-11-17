"""
Workflow Orchestrator
Uses Google ADK to coordinate multiple agents (RetrieveAgent, ActionExtractor, SummarizerAgent) in parallel
"""

from google.adk.agents import Agent
import vertexai
import os
import sys
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Add parent directory to path to import agents
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import agents
try:
    from agents.RetrieveAgent.agent import root_agent as retrieve_agent
    from agents.ActionExtractor.agent import root_agent as action_extractor_agent
    from agents.SummarizerAgent.agent import root_agent as summarizer_agent
except ImportError as e:
    print(f"Warning: Could not import agents: {e}")
    print("Make sure all agents are properly installed")
    retrieve_agent = None
    action_extractor_agent = None
    summarizer_agent = None

# Load environment variables
load_dotenv()

# Initialize Vertex AI with credentials from environment variables
vertexai.init(
    project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)


def run_retrieve_agent(query: str) -> Dict[str, Any]:
    """
    Run the RetrieveAgent
    
    Args:
        query: Query string for the agent
        
    Returns:
        dict: Agent response
    """
    if retrieve_agent is None:
        return {"status": "error", "error_message": "RetrieveAgent not available"}
    
    try:
        result = retrieve_agent.run(query)
        return {
            "status": "success",
            "agent": "RetrieveAgent",
            "query": query,
            "response": str(result)
        }
    except Exception as e:
        return {
            "status": "error",
            "agent": "RetrieveAgent",
            "error_message": str(e)
        }


def run_action_extractor(query: str) -> Dict[str, Any]:
    """
    Run the ActionExtractor agent
    
    Args:
        query: Query string for the agent
        
    Returns:
        dict: Agent response
    """
    if action_extractor_agent is None:
        return {"status": "error", "error_message": "ActionExtractor not available"}
    
    try:
        result = action_extractor_agent.run(query)
        return {
            "status": "success",
            "agent": "ActionExtractor",
            "query": query,
            "response": str(result)
        }
    except Exception as e:
        return {
            "status": "error",
            "agent": "ActionExtractor",
            "error_message": str(e)
        }


def run_summarizer_agent(query: str) -> Dict[str, Any]:
    """
    Run the SummarizerAgent
    
    Args:
        query: Query string for the agent
        
    Returns:
        dict: Agent response
    """
    if summarizer_agent is None:
        return {"status": "error", "error_message": "SummarizerAgent not available"}
    
    try:
        result = summarizer_agent.run(query)
        return {
            "status": "success",
            "agent": "SummarizerAgent",
            "query": query,
            "response": str(result)
        }
    except Exception as e:
        return {
            "status": "error",
            "agent": "SummarizerAgent",
            "error_message": str(e)
        }


def run_agents_parallel(agent_queries: Dict[str, str]) -> Dict[str, Any]:
    """
    Run multiple agents in parallel
    
    Args:
        agent_queries: Dictionary mapping agent names to queries
        Format: {"RetrieveAgent": "query", "ActionExtractor": "query", ...}
        
    Returns:
        dict: Combined results from all agents
    """
    results = {
        "status": "success",
        "agents_executed": [],
        "results": {},
        "errors": {}
    }
    
    # Map agent names to functions
    agent_functions = {
        "RetrieveAgent": run_retrieve_agent,
        "ActionExtractor": run_action_extractor,
        "SummarizerAgent": run_summarizer_agent
    }
    
    # Execute agents in parallel
    with ThreadPoolExecutor(max_workers=len(agent_queries)) as executor:
        # Submit all tasks
        future_to_agent = {
            executor.submit(agent_functions[agent_name], query): agent_name
            for agent_name, query in agent_queries.items()
            if agent_name in agent_functions
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_agent):
            agent_name = future_to_agent[future]
            try:
                result = future.result()
                results["agents_executed"].append(agent_name)
                
                if result.get("status") == "success":
                    results["results"][agent_name] = result
                else:
                    results["errors"][agent_name] = result.get("error_message", "Unknown error")
            except Exception as e:
                results["errors"][agent_name] = str(e)
    
    # Update overall status if any errors occurred
    if results["errors"]:
        results["status"] = "partial_success" if results["results"] else "error"
    
    return results


def orchestrate_workflow(workflow_type: str, **params) -> Dict[str, Any]:
    """
    Orchestrate a complex workflow involving multiple agents in parallel
    
    Args:
        workflow_type: Type of workflow ("analyze_comprehensive", "agent_performance", "text_analysis")
        **params: Workflow-specific parameters
        
    Returns:
        dict: Workflow results
    """
    results = {"workflow_type": workflow_type, "steps": []}
    
    try:
        if workflow_type == "analyze_comprehensive":
            # Comprehensive analysis using all agents in parallel
            text = params.get("text", "")
            agent_id = params.get("agent_id", "retriever")
            
            # Prepare queries for each agent
            agent_queries = {
                "SummarizerAgent": f"Analyze the token usage for this text: '{text}'",
                "RetrieveAgent": f"What are the usage statistics for the {agent_id} agent?",
                "ActionExtractor": f"Extract actions from this text: '{text}'"
            }
            
            # Run all agents in parallel
            parallel_results = run_agents_parallel(agent_queries)
            results["steps"].append({"step": "parallel_agent_execution", "result": parallel_results})
            results["status"] = parallel_results.get("status", "success")
            
        elif workflow_type == "agent_performance":
            # Get agent performance metrics using RetrieveAgent and ActionExtractor
            agent_id = params.get("agent_id", "retriever")
            reasoning_steps = params.get("reasoning_steps", 0)
            tool_calls = params.get("tool_calls", 0)
            tokens = params.get("tokens", 0)
            
            # Prepare queries for parallel execution
            agent_queries = {
                "RetrieveAgent": f"What are the usage statistics for the {agent_id} agent?",
                "ActionExtractor": f"Validate this reasoning chain: {reasoning_steps} steps, {tool_calls} tool calls, {tokens} tokens. Extract the key actions."
            }
            
            # Run agents in parallel
            parallel_results = run_agents_parallel(agent_queries)
            results["steps"].append({"step": "parallel_agent_execution", "result": parallel_results})
            results["status"] = parallel_results.get("status", "success")
            
        elif workflow_type == "text_analysis":
            # Analyze text using SummarizerAgent and ActionExtractor in parallel
            text = params.get("text", "")
            
            # Prepare queries for parallel execution
            agent_queries = {
                "SummarizerAgent": f"Analyze the token usage for this text: '{text}'",
                "ActionExtractor": f"Extract actionable items from this text: '{text}'"
            }
            
            # Run agents in parallel
            parallel_results = run_agents_parallel(agent_queries)
            results["steps"].append({"step": "parallel_agent_execution", "result": parallel_results})
            results["status"] = parallel_results.get("status", "success")
            
        else:
            results["status"] = "error"
            results["error_message"] = f"Unknown workflow type: {workflow_type}"
            
    except Exception as e:
        results["status"] = "error"
        results["error_message"] = str(e)
    
    return results


def check_all_agents() -> Dict[str, Any]:
    """
    Check availability of all agents
    
    Returns:
        dict: Status of all agents
    """
    agent_status = {
        "RetrieveAgent": {"available": retrieve_agent is not None},
        "ActionExtractor": {"available": action_extractor_agent is not None},
        "SummarizerAgent": {"available": summarizer_agent is not None}
    }
    
    all_available = all(status["available"] for status in agent_status.values())
    
    return {
        "status": "all_available" if all_available else "partial",
        "agents": agent_status
    }


# Create the Orchestrator Agent using Google ADK
orchestrator_agent = Agent(
    name="workflow_orchestrator",
    model="gemini-2.5-flash-lite",
    description="An AI orchestrator that coordinates multiple agents (RetrieveAgent, ActionExtractor, SummarizerAgent) in parallel for complex workflows.",
    instruction="""
    You are a Workflow Orchestrator that coordinates multiple agents in parallel for complex workflows.
    
    Available Agents:
    1. **RetrieveAgent**: Retrieves agent usage statistics from AgentInventory MCP
    2. **ActionExtractor**: Extracts actions from reasoning chains and validates reasoning cost
    3. **SummarizerAgent**: Analyzes token usage statistics from TokenStats MCP
    
    Your capabilities include:
    1. Orchestrating parallel execution of multiple agents
    2. Coordinating workflows that require multiple agent capabilities
    3. Combining results from different agents into comprehensive insights
    4. Managing agent execution and error handling
    
    Available Workflows:
    1. **analyze_comprehensive**: Comprehensive analysis using all agents in parallel
       - SummarizerAgent: Token usage analysis
       - RetrieveAgent: Agent performance metrics
       - ActionExtractor: Action extraction
    
    2. **agent_performance**: Agent performance analysis using RetrieveAgent and ActionExtractor
       - RetrieveAgent: Usage statistics
       - ActionExtractor: Reasoning validation and action extraction
    
    3. **text_analysis**: Text analysis using SummarizerAgent and ActionExtractor
       - SummarizerAgent: Token statistics
       - ActionExtractor: Action extraction
    
    When orchestrating workflows:
    1. Use the orchestrate_workflow function with appropriate workflow type
    2. Run agents in parallel for efficiency
    3. Combine and synthesize results from multiple agents
    4. Provide clear summaries of parallel execution results
    5. Handle errors gracefully and report which agents succeeded/failed
    
    When users ask about agent capabilities:
    1. Use check_all_agents to verify agent availability
    2. Explain what each agent does
    3. Suggest appropriate workflows based on user needs
    
    Always be helpful, clear, and provide comprehensive summaries of orchestrated workflows.
    """,
    tools=[
        run_retrieve_agent,
        run_action_extractor,
        run_summarizer_agent,
        run_agents_parallel,
        orchestrate_workflow,
        check_all_agents
    ]
)


if __name__ == "__main__":
    # Example usage
    print("Workflow Orchestrator")
    print("=" * 60)
    print()
    
    # Check all agents
    print("Checking all agents...")
    agent_status = check_all_agents()
    for agent_name, status in agent_status["agents"].items():
        status_symbol = "✅" if status["available"] else "❌"
        print(f"{status_symbol} {agent_name}: {'Available' if status['available'] else 'Not Available'}")
    print()
    
    # Example orchestration
    if agent_status["status"] == "all_available":
        print("Example: Orchestrating comprehensive analysis workflow...")
        result = orchestrate_workflow(
            "analyze_comprehensive",
            text="The quick brown fox jumps over the lazy dog.",
            agent_id="retriever"
        )
        print(f"Status: {result.get('status')}")
        for step in result.get("steps", []):
            print(f"\nStep: {step.get('step')}")
            step_result = step.get("result", {})
            if step_result.get("status") == "success":
                print(f"  Agents executed: {step_result.get('agents_executed')}")
                for agent, agent_result in step_result.get("results", {}).items():
                    print(f"  ✅ {agent}: Success")
    else:
        print("⚠️  Some agents are not available. Please ensure all agents are properly installed.")
