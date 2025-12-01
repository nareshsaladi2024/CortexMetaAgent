"""
AutoEvalAgent
Uses Google ADK to automatically generate evaluation suites and run regression tests for agents
"""

from google.adk.agents import Agent
import vertexai
import os
import sys
import requests
import json
import random
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from concurrent.futures import ThreadPoolExecutor, as_completed

# Import evaluator - use relative import for better compatibility
try:
    from .evaluator import run_adk_cli_eval
except ImportError:
    # Fallback to absolute import if relative import fails
    from evaluator import run_adk_cli_eval

# Add parent directory to path to import utilities and config
# Try to import config, but handle gracefully if not available (e.g., in deployed environment)
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

try:
    from config import AGENT_MODEL, MCP_AGENT_INVENTORY_URL
except ImportError:
    # Fallback for deployed environments where config.py might not be available
    # Use environment variables directly
    AGENT_MODEL = os.environ.get("AGENT_MODEL", "gemini-2.5-flash-lite")
    MCP_AGENT_INVENTORY_URL = os.environ.get("MCP_AGENT_INVENTORY_URL", "http://localhost:8001")

# Import MetricsAgent's list_agents function for delegation
try:
    from agents.MetricsAgent.agent import list_agents as metrics_list_agents
except ImportError:
    # Fallback if MetricsAgent not available
    metrics_list_agents = None

# Load environment variables from shared .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Initialize Vertex AI with credentials from environment variables
vertexai.init(
    project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)

# MCP Server URLs from config (already imported above)


def list_agents_from_inventory(mcp_server_url: Optional[str] = None) -> Dict[str, Any]:
    """
    List all agents from AgentInventory MCP server.
    
    This function delegates to MetricsAgent through CortexMetaAgent architecture.
    MetricsAgent handles all MCP server interactions for agent inventory.
    
    Args:
        mcp_server_url: URL of the AgentInventory MCP server (optional, passed to MetricsAgent)
    
    Returns:
        dict: List of agents with status, agents list, and total_count
    """
    # Delegate to MetricsAgent's list_agents function
    if metrics_list_agents is None:
        return {
            "status": "error",
            "error_message": "MetricsAgent not available. Cannot list agents.",
            "agents": []
        }
    
    try:
        # Call MetricsAgent's list_agents function
        result = metrics_list_agents(mcp_server_url=mcp_server_url, include_deployed=False)
        
        # Ensure consistent return format
        if result.get("status") == "success":
            return {
                "status": "success",
                "agents": result.get("agents", []),
                "total_count": result.get("total_count", len(result.get("agents", [])))
            }
        else:
            return result
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error delegating to MetricsAgent: {str(e)}",
            "agents": []
        }


def generate_eval_set(agent_id: str, set_type: str, count: int = None, force_regenerate: bool = False) -> Dict[str, Any]:
    """
    Generate evaluation set for an agent dynamically using LLM.
    Will skip if eval set already exists (unless force_regenerate=True).
    
    Args:
        agent_id: The ID of the agent to generate eval set for
        set_type: Type of eval set ("positive", "negative", "adversarial", "stress")
        count: Number of examples to generate (optional, uses defaults if not provided)
        force_regenerate: If True, regenerate even if eval set exists (default: False)
    
    Returns:
        dict: Generated evaluation set information
    """
    # Default counts
    default_counts = {
        "positive": 1000,
        "negative": 600,
        "adversarial": 400,
        "stress": 1000
    }
    
    if count is None:
        count = default_counts.get(set_type, 100)
    
    try:
        # Import the eval set generator (uses LLM)
        from generate_eval_sets import generate_eval_set as generate_set
        
        result = generate_set(agent_id, set_type, count, force_regenerate=force_regenerate)
        
        # Handle skipped status
        if result.get("status") == "skipped":
            return result
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "set_type": set_type,
            "count": count,
            "method": "dynamic_llm",
            "output_file_jsonl": result.get("output_file_jsonl"),
            "output_file_evalset": result.get("output_file_evalset"),
            "generated": result.get("generated", 0)
        }
    except ImportError:
        # Fallback: basic generation without full generator
        return {
            "status": "error",
            "error_message": "generate_eval_sets module not found",
            "agent_id": agent_id,
            "set_type": set_type,
            "count": count
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "agent_id": agent_id,
            "set_type": set_type
        }


def run_eval_suite(agent_id: str, suite_path: str, method: str = "adk_cli") -> Dict[str, Any]:
    """
    Run evaluation suite for an agent using ADK CLI
    
    Args:
        agent_id: The ID of the agent to evaluate
        suite_path: Path to the evaluation suite directory or file
        method: Evaluation method (default: "adk_cli", only ADK CLI is supported)
    
    Returns:
        dict: Evaluation results
    """
    if method != "adk_cli":
        return {
            "status": "error",
            "error_message": f"Only 'adk_cli' method is supported. Got: {method}",
            "agent_id": agent_id,
            "suite_path": suite_path,
            "method": method
        }
    
    try:
        # Use ADK CLI eval
        results = run_adk_cli_eval(agent_id, suite_path)
        return {
            "status": "success",
            "agent_id": agent_id,
            "suite_path": suite_path,
            "method": "adk_cli",
            "results": results
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "agent_id": agent_id,
            "suite_path": suite_path,
            "method": "adk_cli"
        }


def create_eval_set_for_new_agent(agent_id: str, generate_dynamically: bool = True, force_regenerate: bool = False) -> Dict[str, Any]:
    """
    Create evaluation sets for a new agent dynamically using LLM.
    NOTE: This will skip generation if eval sets already exist (unless force_regenerate=True).
    
    Args:
        agent_id: The ID of the new agent
        generate_dynamically: Whether to generate dynamically using LLM (default: True)
        force_regenerate: If True, regenerate even if eval sets exist (default: False)
    
    Returns:
        dict: Results of eval set creation
    """
    results = {
        "status": "success",
        "agent_id": agent_id,
        "method": "dynamic_llm" if generate_dynamically else "static",
        "sets_created": [],
        "sets_skipped": [],
        "errors": []
    }
    
    # Check if agent exists in inventory
    agents = list_agents_from_inventory()
    agent_exists = False
    agent_description = None
    
    if agents.get("status") == "success":
        for agent in agents.get("agents", []):
            if agent.get("id") == agent_id:
                agent_exists = True
                agent_description = agent.get("description")
                break
    
    # For new agents, we still generate dynamically based on success scenarios
    # The LLM will generate different prompts based on the agent's purpose
    if not agent_exists and generate_dynamically:
        # Agent doesn't exist yet - use a generic description
        # The LLM will generate test cases based on this and the agent_id
        agent_description = f"Agent {agent_id}"
    
    # Generate all four types of eval sets dynamically
    set_types = ["positive", "negative", "adversarial", "stress"]
    default_counts = {
        "positive": 1000,
        "negative": 600,
        "adversarial": 400,
        "stress": 1000
    }
    
    for set_type in set_types:
        try:
            count = default_counts.get(set_type, 100)
            result = generate_eval_set(agent_id, set_type, count)
            
            if result.get("status") == "success":
                results["sets_created"].append({
                    "type": set_type,
                    "count": result.get("generated", 0),
                    "file_jsonl": result.get("output_file_jsonl"),
                    "file_evalset": result.get("output_file_evalset")
                })
            elif result.get("status") == "skipped":
                results["sets_skipped"].append({
                    "type": set_type,
                    "message": result.get("message", "Eval set already exists")
                })
            else:
                results["errors"].append({
                    "type": set_type,
                    "error": result.get("error_message", "Unknown error")
                })
        except Exception as e:
            results["errors"].append({
                "type": set_type,
                "error": str(e)
            })
    
    # Update status based on results
    if results["errors"] and not results["sets_created"]:
        results["status"] = "error"
    elif results["errors"]:
        results["status"] = "partial_success"
    elif results["sets_skipped"] and not results["sets_created"]:
        results["status"] = "skipped"
    
    return results


def run_regression_test(agent_id: str, eval_suite_dir: Optional[str] = None, method: str = "adk_cli") -> Dict[str, Any]:
    """
    Run regression test when agent code or configuration changes using ADK CLI
    
    Args:
        agent_id: The ID of the agent to test
        eval_suite_dir: Directory containing eval suites (optional)
        method: Evaluation method (default: "adk_cli", only ADK CLI is supported)
    
    Returns:
        dict: Regression test results
    """
    if method != "adk_cli":
        return {
            "status": "error",
            "error_message": f"Only 'adk_cli' method is supported. Got: {method}",
            "agent_id": agent_id,
            "suite_dir": eval_suite_dir or f"eval_suites/{agent_id}"
        }
    
    if not eval_suite_dir:
        eval_suite_dir = f"eval_suites/{agent_id}"
    
    results = {
        "status": "success",
        "agent_id": agent_id,
        "suite_dir": eval_suite_dir,
        "method": "adk_cli",
        "test_results": {},
        "summary": {}
    }
    
    # Run ADK CLI eval on the entire suite directory
    try:
        result = run_eval_suite(agent_id, eval_suite_dir, method="adk_cli")
        results["test_results"]["adk_cli"] = result
        
        # Calculate summary from ADK CLI results
        if result.get("status") == "success":
            test_result = result.get("results", {})
            total = test_result.get("total", 0)
            passed = test_result.get("passed", 0)
            failed = test_result.get("failed", 0)
            
            results["summary"] = {
                "total_tests": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": round((passed / total * 100), 2) if total > 0 else 0
            }
        else:
            results["summary"] = {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0
            }
    except Exception as e:
        results["test_results"]["adk_cli"] = {
            "status": "error",
            "error_message": str(e)
        }
        results["summary"] = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "pass_rate": 0
        }
    
    return results


# Create the AutoEval Agent using Google ADK
auto_eval_agent = Agent(
    name="AutoEvalAgent",
    model=AGENT_MODEL,  # From global config (default: gemini-2.5-flash-lite)
    description="An AI agent that automatically generates evaluation suites for agents and runs regression tests when agent code or configuration changes.",
    instruction="""
    You are an AutoEvalAgent that manages evaluation suites for AI agents.
    
    Your capabilities include:
    1. Listing all agents by delegating to MetricsAgent (which queries AgentInventory MCP server)
    2. Creating evaluation sets for new agents automatically
    3. Generating four types of eval sets:
       - Positive: Valid tasks (multi-doc QA, summarization, classification, extraction)
       - Negative: Corrupt JSON, reversed instructions, misleading labels, token-limit overflow
       - Adversarial: Contradictory facts, distractor paragraphs, random noise, Unicode edge cases
       - Stress: 10k prompts at 512-4096 tokens, long-context chains, deep reasoning (10+ steps)
    4. Running regression tests when agent code or configuration changes
    5. Validating test results:
       - Negative tests → expects FAIL
       - Positive tests → expects PASS
       - Adversarial tests → expects "consistent & hallucination-free"
    
    When creating eval sets for a new agent:
    1. IMPORTANT: Do NOT write eval sets for existing agents - check if eval sets already exist first
    2. Use list_agents_from_inventory (which delegates to MetricsAgent) to check the agent's capabilities and description
    3. Use create_eval_set_for_new_agent to generate all four eval set types dynamically using LLM
    4. The LLM generates different prompts and expected responses based on:
       - Agent's description and capabilities from the inventory
       - Success scenarios for the agent's domain
       - Diverse task types (multi-doc QA, summarization, classification, extraction)
    5. Each generation creates unique, diverse test cases relevant to the agent's purpose
    6. Generate eval sets on-the-fly - they are created dynamically, not from templates
    7. If eval sets already exist, skip generation unless explicitly requested to regenerate
    8. Confirm generation of positive.jsonl (1000), negative.jsonl (600), adversarial.jsonl (400), stress.jsonl (1000)
    
    When running regression tests:
    1. Use run_regression_test with the agent_id (uses ADK CLI by default)
    2. Uses ADK CLI eval command for Google ADK evaluation
    3. Validate results according to expectations:
       - Positive tests should PASS
       - Negative tests should FAIL
       - Adversarial tests should be consistent and hallucination-free
    4. Report pass rates and any failures
    
    Always be thorough, accurate, and provide detailed reports on evaluation results.
    """,
    tools=[
        list_agents_from_inventory,
        generate_eval_set,
        create_eval_set_for_new_agent,
        run_eval_suite,
        run_regression_test
    ]
)


if __name__ == "__main__":
    # Example usage
    print("AutoEvalAgent")
    print("=" * 60)
    print()
    
    # List agents
    print("Listing agents from inventory...")
    agents = list_agents_from_inventory()
    if agents.get("status") == "success":
        print(f"Found {agents.get('total_count', 0)} agents")
        for agent in agents.get("agents", [])[:5]:  # Show first 5
            print(f"  - {agent.get('id')}: {agent.get('description', 'No description')}")
    print()
    
    # Example: Create eval sets for a new agent
    print("Example: Creating eval sets for retriever agent...")
    result = auto_eval_agent.run("Create evaluation sets for the retriever agent")
    print(result)

