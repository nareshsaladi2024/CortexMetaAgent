"""
RetrieveAgent
Uses Google ADK to create an agent that queries agent usage statistics from AgentInventory MCP server
"""

from google.adk.agents import Agent
import vertexai
import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

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


def get_agent_usage(agent_id: str = "retriever", mcp_server_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Get usage statistics for an agent from the AgentInventory MCP server
    
    This tool queries the AgentInventory MCP server to get:
    - Total runs
    - Failures
    - Average input/output tokens
    - Latency percentiles (p50, p95)
    
    Args:
        agent_id: The ID of the agent (default: "retriever")
        mcp_server_url: URL of the AgentInventory MCP server (optional)
    
    Returns:
        dict: Dictionary containing usage statistics
    """
    # Get MCP server URL from environment or use default
    if not mcp_server_url:
        mcp_server_url = os.environ.get("MCP_AGENT_INVENTORY_URL", "http://localhost:8001")
    
    usage_endpoint = f"{mcp_server_url}/usage"
    
    try:
        # Make request to MCP server with query parameter
        response = requests.get(
            usage_endpoint,
            params={"agent": agent_id},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Raise exception if request failed
        response.raise_for_status()
        
        # Return usage statistics
        usage = response.json()
        return {
            "status": "success",
            "agent_id": agent_id,
            "total_runs": usage.get("total_runs", 0),
            "failures": usage.get("failures", 0),
            "avg_input_tokens": usage.get("avg_input_tokens", 0.0),
            "avg_output_tokens": usage.get("avg_output_tokens", 0.0),
            "p50_latency_ms": usage.get("p50_latency_ms", 0.0),
            "p95_latency_ms": usage.get("p95_latency_ms", 0.0),
            "success_rate": round(((usage.get("total_runs", 0) - usage.get("failures", 0)) / usage.get("total_runs", 1)) * 100, 2) if usage.get("total_runs", 0) > 0 else 0.0
        }
        
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "error_message": f"Cannot connect to AgentInventory MCP server at {mcp_server_url}. Make sure the server is running.",
            "agent_id": agent_id
        }
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_message": "Request to AgentInventory MCP server timed out. Please try again.",
            "agent_id": agent_id
        }
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {
                "status": "error",
                "error_message": f"Agent {agent_id} not found in inventory. Make sure the agent is registered.",
                "agent_id": agent_id
            }
        return {
            "status": "error",
            "error_message": f"AgentInventory MCP server returned error: {e.response.status_code} - {e.response.text}",
            "agent_id": agent_id
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error: {str(e)}",
            "agent_id": agent_id
        }


def list_agents(mcp_server_url: Optional[str] = None) -> Dict[str, Any]:
    """
    List all agents in the AgentInventory MCP server
    
    Args:
        mcp_server_url: URL of the AgentInventory MCP server (optional)
    
    Returns:
        dict: Dictionary containing list of agents
    """
    # Get MCP server URL from environment or use default
    if not mcp_server_url:
        mcp_server_url = os.environ.get("MCP_AGENT_INVENTORY_URL", "http://localhost:8001")
    
    list_endpoint = f"{mcp_server_url}/list_agents"
    
    try:
        response = requests.get(
            list_endpoint,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        return {
            "status": "success",
            "agents": data.get("agents", []),
            "total_count": data.get("total_count", len(data.get("agents", [])))
        }
        
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "error_message": f"Cannot connect to AgentInventory MCP server at {mcp_server_url}. Make sure the server is running.",
            "agents": []
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error: {str(e)}",
            "agents": []
        }


def check_agent_inventory_health(mcp_server_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Check if the AgentInventory MCP server is running and healthy.
    
    Args:
        mcp_server_url: URL of the AgentInventory MCP server (optional)
    
    Returns:
        dict: Dictionary containing server health status
    """
    if not mcp_server_url:
        mcp_server_url = os.environ.get("MCP_AGENT_INVENTORY_URL", "http://localhost:8001")
    
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
            "error_message": f"Cannot connect to AgentInventory MCP server at {mcp_server_url}. Make sure the server is running."
        }
    except Exception as e:
        return {
            "status": "error",
            "server_url": mcp_server_url,
            "error_message": f"Error checking server health: {str(e)}"
        }


# Create the AI Agent using Google ADK
root_agent = Agent(
    name="retrieve_agent",
    model="gemini-2.5-flash-lite",  # Fast, cost-effective Gemini model
    description="An AI agent that retrieves and analyzes agent usage statistics from the AgentInventory MCP server. Specializes in querying agent performance metrics including usage patterns, latency, and failure rates.",
    instruction="""
    You are a RetrieveAgent that specializes in retrieving and analyzing agent usage statistics from the AgentInventory MCP server.
    
    Your capabilities include:
    1. Retrieving usage statistics for specific agents (especially the retriever agent)
    2. Listing all available agents in the inventory
    3. Analyzing agent performance metrics including:
       - Total runs and failure counts
       - Average input/output tokens
       - Latency percentiles (p50, p95)
       - Success rates
    4. Providing insights about agent performance and identifying bottlenecks
    
    When users ask about agent usage:
    1. Use the get_agent_usage tool to query the AgentInventory MCP server
    2. By default, query for the "retriever" agent, but support other agents too
    3. Present the results clearly, including:
       - Total runs and failures
       - Success rate percentage
       - Average token usage
       - Latency metrics (p50, p95)
    4. Provide helpful analysis of the metrics
    
    When users ask to list agents:
    1. Use the list_agents tool to get all available agents
    2. Present the list with descriptions and metadata
    
    If the MCP server is not available:
    1. Use the check_agent_inventory_health tool to diagnose the issue
    2. Provide helpful guidance on how to start the server
    3. Suggest alternative approaches if possible
    
    Always be helpful, clear, and concise. Format statistics in a readable way with proper units.
    """,
    tools=[get_agent_usage, list_agents, check_agent_inventory_health]
)


if __name__ == "__main__":
    # Example usage
    print("RetrieveAgent")
    print("=" * 50)
    print()
    
    # Check server health
    print("Checking AgentInventory MCP server health...")
    health = check_agent_inventory_health()
    print(f"Status: {health.get('status')}")
    if health.get('error_message'):
        print(f"Error: {health.get('error_message')}")
    print()
    
    # Example query
    if health.get("status") == "healthy":
        print("Example: Getting retriever agent usage...")
        result = root_agent.run("What are the usage statistics for the retriever agent?")
        print(result)
    else:
        print("⚠️  AgentInventory MCP server is not running. Please start it with:")
        print("   cd ../../mcp-servers/mcp-agent-inventory")
        print("   python server.py")
        print("   or")
        print("   .\\run-server.ps1")

