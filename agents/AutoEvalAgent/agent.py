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
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from evaluator import run_adk_cli_eval, run_evaluation_pytest as run_pytest_eval
# Add parent directory to path to import utilities and config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import AGENT_MODEL, MCP_AGENT_INVENTORY_URL, MCP_TOKENSTATS_URL

# Load environment variables
load_dotenv()

# Initialize Vertex AI with credentials from environment variables
vertexai.init(
    project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)

# MCP Server URLs from config (already imported above)


def list_agents_from_inventory(mcp_server_url: Optional[str] = None) -> Dict[str, Any]:
    """
    List all agents from AgentInventory MCP server
    
    Args:
        mcp_server_url: URL of the AgentInventory MCP server (optional)
    
    Returns:
        dict: List of agents
    """
    if not mcp_server_url:
        mcp_server_url = os.environ.get("MCP_AGENT_INVENTORY_URL", "http://localhost:8001")
    
    try:
        response = requests.get(
            f"{mcp_server_url}/list_agents",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "status": "success",
            "agents": data.get("agents", []),
            "total_count": data.get("total_count", len(data.get("agents", [])))
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "agents": []
        }


def check_token_limit(prompt: str, max_tokens: int = 4096, mcp_server_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Check if prompt exceeds token limit using TokenStats MCP
    
    Args:
        prompt: The text prompt to check
        max_tokens: Maximum allowed tokens
        mcp_server_url: URL of the TokenStats MCP server (optional)
    
    Returns:
        dict: Token count and whether it exceeds limit
    """
    if not mcp_server_url:
        mcp_server_url = MCP_TOKENSTATS_URL
    
    try:
        response = requests.post(
            f"{mcp_server_url}/tokenize",
            json={"model": "gemini-2.5-flash", "prompt": prompt},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        input_tokens = data.get("input_tokens", 0)
        exceeds_limit = input_tokens > max_tokens
        
        return {
            "status": "success",
            "input_tokens": input_tokens,
            "max_tokens": max_tokens,
            "exceeds_limit": exceeds_limit,
            "within_limit": not exceeds_limit
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "exceeds_limit": False
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


def run_eval_suite(agent_id: str, suite_path: str, method: str = "pytest") -> Dict[str, Any]:
    """
    Run evaluation suite for an agent using pytest or ADK CLI
    
    Args:
        agent_id: The ID of the agent to evaluate
        suite_path: Path to the evaluation suite directory or file
        method: Evaluation method ("pytest" or "adk_cli")
    
    Returns:
        dict: Evaluation results
    """
    try:
        # Import the evaluator
        from evaluator import run_evaluation
        
        results = run_evaluation(agent_id, suite_path, method=method)
        return {
            "status": "success",
            "agent_id": agent_id,
            "suite_path": suite_path,
            "method": method,
            "results": results
        }
    except ImportError:
        return {
            "status": "error",
            "error_message": "evaluator module not found",
            "agent_id": agent_id,
            "suite_path": suite_path,
            "method": method
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "agent_id": agent_id,
            "method": method
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


def run_regression_test(agent_id: str, eval_suite_dir: Optional[str] = None, method: str = "pytest") -> Dict[str, Any]:
    """
    Run regression test when agent code or configuration changes
    
    Args:
        agent_id: The ID of the agent to test
        eval_suite_dir: Directory containing eval suites (optional)
        method: Evaluation method ("pytest" or "adk_cli")
    
    Returns:
        dict: Regression test results
    """
    if not eval_suite_dir:
        eval_suite_dir = f"eval_suites/{agent_id}"
    
    results = {
        "status": "success",
        "agent_id": agent_id,
        "suite_dir": eval_suite_dir,
        "method": method,
        "test_results": {},
        "summary": {}
    }
    
    # Run all eval sets
    if method == "pytest":
        # Run pytest on the entire suite directory
        try:
            import subprocess
            import sys
            
            # Run pytest with the test file
            test_file = os.path.join(os.path.dirname(__file__), "test_eval_pytest.py")
            cmd = [
                sys.executable, "-m", "pytest",
                test_file,
                "--agent-id", agent_id,
                "--eval-suite-dir", os.path.dirname(eval_suite_dir) if os.path.dirname(eval_suite_dir) else "eval_suites",
                "-v"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            results["test_results"]["pytest"] = {
                "status": "success" if result.returncode == 0 else "error",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            results["test_results"]["pytest"] = {
                "status": "error",
                "error_message": str(e)
            }
    else:
        # Run ADK CLI eval on the entire suite directory
        result = run_eval_suite(agent_id, eval_suite_dir, method="adk_cli")
        results["test_results"]["adk_cli"] = result
    
    # Calculate summary
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for method_name, result in results["test_results"].items():
        if result.get("status") == "success":
            if method_name == "pytest":
                # Parse pytest output
                stdout = result.get("stdout", "")
                # Simple parsing - in production, use pytest JSON output
                if "passed" in stdout.lower():
                    passed_tests += stdout.lower().count("passed")
                    failed_tests += stdout.lower().count("failed")
                    total_tests = passed_tests + failed_tests
            else:
                test_result = result.get("results", {})
                total = test_result.get("total", 0)
                passed = test_result.get("passed", 0)
                failed = test_result.get("failed", 0)
                
                total_tests += total
                passed_tests += passed
                failed_tests += failed
    
    results["summary"] = {
        "total_tests": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "pass_rate": round((passed_tests / total_tests * 100), 2) if total_tests > 0 else 0
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
    1. Listing all agents from the AgentInventory MCP server
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
    2. Use list_agents_from_inventory to check the agent's capabilities and description
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
    1. Use run_regression_test with the agent_id and method ("pytest" or "adk_cli")
    2. Support both evaluation methods:
       - pytest: Uses pytest framework for Python-based testing
       - adk_cli: Uses ADK CLI eval command for Google ADK evaluation
    3. Validate results according to expectations:
       - Positive tests should PASS
       - Negative tests should FAIL
       - Adversarial tests should be consistent and hallucination-free
    4. Report pass rates and any failures
    
    When checking token limits:
    1. Use check_token_limit to verify prompts don't exceed limits
    2. Use TokenStats MCP to get accurate token counts
    
    Always be thorough, accurate, and provide detailed reports on evaluation results.
    """,
    tools=[
        list_agents_from_inventory,
        check_token_limit,
        generate_eval_set,
        create_eval_set_for_new_agent,
        run_eval_suite,
        run_regression_test,
        run_adk_cli_eval,
        run_pytest_eval
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

