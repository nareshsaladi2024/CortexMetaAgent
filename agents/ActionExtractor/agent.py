"""
ActionExtractor Agent
Uses Google ADK to extract actions from reasoning chains, with ReasoningCost MCP validation
"""

from google.adk.agents import Agent
import vertexai
import os
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Initialize Vertex AI with credentials from environment variables
# Google Cloud SDK will automatically use Application Default Credentials (ADC)
# which can be set via:
# 1. GOOGLE_APPLICATION_CREDENTIALS pointing to a service account JSON file
# 2. gcloud auth application-default login
# 3. Or running on GCP with default service account

vertexai.init(
    project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)


def estimate_reasoning_cost(
    steps: int,
    tool_calls: int,
    tokens_in_trace: int,
    mcp_server_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Estimate reasoning cost using the ReasoningCost MCP server
    
    This tool validates reasoning chains by analyzing:
    - Reasoning depth (number of steps)
    - Tool invocations
    - Token expansion
    
    Args:
        steps: Number of reasoning steps in the chain
        tool_calls: Number of tool invocations made
        tokens_in_trace: Total tokens used in the reasoning trace
        mcp_server_url: URL of the ReasoningCost MCP server (optional)
    
    Returns:
        dict: Dictionary containing cost estimate with:
            - reasoning_depth: Number of reasoning steps
            - tool_invocations: Number of tool invocations
            - expansion_factor: Token expansion factor
            - cost_score: Overall cost score (0.0-1.0+)
    """
    # Get MCP server URL from environment or use default
    if not mcp_server_url:
        mcp_server_url = os.environ.get("MCP_REASONING_COST_URL", "http://localhost:8002")
    
    estimate_endpoint = f"{mcp_server_url}/estimate"
    
    try:
        # Make request to MCP server
        response = requests.post(
            estimate_endpoint,
            json={
                "trace": {
                    "steps": steps,
                    "tool_calls": tool_calls,
                    "tokens_in_trace": tokens_in_trace
                }
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Raise exception if request failed
        response.raise_for_status()
        
        # Return cost estimate
        estimate = response.json()
        return {
            "status": "success",
            "reasoning_depth": estimate.get("reasoning_depth", steps),
            "tool_invocations": estimate.get("tool_invocations", tool_calls),
            "expansion_factor": estimate.get("expansion_factor", 1.0),
            "cost_score": estimate.get("cost_score", 0.0),
            "validation": "passed" if estimate.get("cost_score", 0.0) < 1.0 else "warning"
        }
        
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "error_message": f"Cannot connect to ReasoningCost MCP server at {mcp_server_url}. Make sure the server is running.",
            "reasoning_depth": steps,
            "tool_invocations": tool_calls,
            "cost_score": 0.0,
            "validation": "unknown"
        }
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_message": "Request to ReasoningCost MCP server timed out. Please try again.",
            "reasoning_depth": steps,
            "tool_invocations": tool_calls,
            "cost_score": 0.0,
            "validation": "unknown"
        }
    except requests.exceptions.HTTPError as e:
        return {
            "status": "error",
            "error_message": f"ReasoningCost MCP server returned error: {e.response.status_code} - {e.response.text}",
            "reasoning_depth": steps,
            "tool_invocations": tool_calls,
            "cost_score": 0.0,
            "validation": "unknown"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error: {str(e)}",
            "reasoning_depth": steps,
            "tool_invocations": tool_calls,
            "cost_score": 0.0,
            "validation": "unknown"
        }


def check_reasoning_cost_health(mcp_server_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Check if the ReasoningCost MCP server is running and healthy.
    
    Args:
        mcp_server_url: URL of the ReasoningCost MCP server (optional)
    
    Returns:
        dict: Dictionary containing server health status
    """
    if not mcp_server_url:
        mcp_server_url = os.environ.get("MCP_REASONING_COST_URL", "http://localhost:8002")
    
    health_endpoint = f"{mcp_server_url}/health"
    
    try:
        response = requests.get(health_endpoint, timeout=5)
        response.raise_for_status()
        health_data = response.json()
        
        return {
            "status": "healthy",
            "server_url": mcp_server_url,
            "health_check": health_data
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "unhealthy",
            "server_url": mcp_server_url,
            "error_message": f"Cannot connect to ReasoningCost MCP server at {mcp_server_url}. Make sure the server is running."
        }
    except Exception as e:
        return {
            "status": "error",
            "server_url": mcp_server_url,
            "error_message": f"Error checking server health: {str(e)}"
        }


# Create the AI Agent using Google ADK
root_agent = Agent(
    name="action_extractor",
    model="gemini-2.5-flash-lite",  # Fast, cost-effective Gemini model
    description="An AI agent that extracts actionable items from reasoning chains and validates reasoning cost using the ReasoningCost MCP server.",
    instruction="""
    You are an ActionExtractor agent that analyzes reasoning chains to:
    1. Extract actionable items and steps from reasoning processes
    2. Validate reasoning chains for cost efficiency using the ReasoningCost MCP server
    3. Identify and flag expensive or runaway reasoning patterns
    
    When processing reasoning chains:
    1. Analyze the reasoning steps to extract key actions and decisions
    2. Use the estimate_reasoning_cost tool to validate the reasoning chain's cost
    3. Present the extracted actions clearly and concisely
    4. Include cost validation information:
       - If cost_score < 0.6: Reasoning is cost-efficient
       - If cost_score >= 0.6 and < 1.0: Reasoning is moderately expensive
       - If cost_score >= 1.0: Warning - Runaway reasoning detected
    
    When asked about reasoning validation:
    1. Use the estimate_reasoning_cost tool with the provided metrics
    2. Interpret the results clearly
    3. Provide recommendations if reasoning is too expensive
    
    Always be helpful, clear, and concise. Format actions in a structured way for easy understanding.
    """,
    tools=[estimate_reasoning_cost, check_reasoning_cost_health]
)


if __name__ == "__main__":
    # Example usage
    print("ActionExtractor Agent")
    print("=" * 50)
    print()
    
    # Check server health
    print("Checking ReasoningCost MCP server health...")
    health = check_reasoning_cost_health()
    print(f"Status: {health.get('status')}")
    if health.get('error_message'):
        print(f"Warning: {health.get('error_message')}")
    print()
    
    # Example query
    if health.get("status") == "healthy":
        print("Example: Validating a reasoning chain...")
        result = root_agent.run(
            "Validate this reasoning chain: 8 steps, 3 tool calls, 1189 tokens. "
            "Extract the key actions from this reasoning process."
        )
        print(result)
    else:
        print("⚠️  ReasoningCost MCP server is not running. Please start it with:")
        print("   cd ../mcp-servers/mcp-reasoning-cost")
        print("   python server.py")
        print("   or")
        print("   .\\run-server.ps1")

