"""
MetricsAgent
Uses Google ADK to create an agent that queries agent usage statistics and metrics from AgentInventory MCP server
"""

from google.adk.agents import Agent
import vertexai
import os
import sys
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Add parent directory to path to import config
# Add parent directory to path to import config
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)
from config import AGENT_MODEL, MCP_AGENT_INVENTORY_URL

# Load environment variables from shared .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

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
    Get usage statistics for an agent from the mcp-agent-inventory MCP server.
    
    This tool queries the mcp-agent-inventory MCP server to get:
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
    # Get MCP server URL from config or parameter
    if not mcp_server_url:
        mcp_server_url = MCP_AGENT_INVENTORY_URL
    
    # Use the new endpoint: /local/agents/{agent_id}/usage
    usage_endpoint = f"{mcp_server_url}/local/agents/{agent_id}/usage"
    
    try:
        # Make request to MCP server
        response = requests.get(
            usage_endpoint,
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
            "error_message": f"Cannot connect to mcp-agent-inventory MCP server at {mcp_server_url}. Make sure the server is running.",
            "agent_id": agent_id
        }
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_message": "Request to mcp-agent-inventory MCP server timed out. Please try again.",
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
            "error_message": f"mcp-agent-inventory MCP server returned error: {e.response.status_code} - {e.response.text}",
            "agent_id": agent_id
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error: {str(e)}",
            "agent_id": agent_id
        }


def list_agents(mcp_server_url: Optional[str] = None, include_deployed: bool = False) -> Dict[str, Any]:
    """
    List all agents from the mcp-agent-inventory MCP server.
    
    Can list both local agents and deployed agents (GCP Reasoning Engine).
    
    Args:
        mcp_server_url: URL of the AgentInventory MCP server (optional)
        include_deployed: If True, also include deployed agents from GCP Reasoning Engine
    
    Returns:
        dict: Dictionary containing list of agents
    """
    # Get MCP server URL from config or parameter
    if not mcp_server_url:
        mcp_server_url = MCP_AGENT_INVENTORY_URL
    
    try:
        # Use the new endpoint: /local/agents
        list_endpoint = f"{mcp_server_url}/local/agents"
        
        response = requests.get(
            list_endpoint,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        response.raise_for_status()
        data = response.json()
        
        result = {
            "status": "success",
            "agents": data.get("agents", []),
            "total_count": len(data.get("agents", []))
        }
        
        # If include_deployed is True, also get deployed agents
        if include_deployed:
            try:
                deployed_endpoint = f"{mcp_server_url}/deployed/agents"
                deployed_response = requests.get(
                    deployed_endpoint,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if deployed_response.status_code == 200:
                    deployed_data = deployed_response.json()
                    deployed_agents = deployed_data.get("agents", [])
                    result["deployed_agents"] = deployed_agents
                    result["deployed_count"] = len(deployed_agents)
            except Exception:
                # If deployed agents can't be fetched, continue with local agents only
                pass
        
        return result
        
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "error_message": f"Cannot connect to mcp-agent-inventory MCP server at {mcp_server_url}. Make sure the server is running.",
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
    Check if the mcp-agent-inventory MCP server is running and healthy.
    
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
            "server_type": "mcp-agent-inventory",
            "health_check": health_data
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "unhealthy",
            "server_url": mcp_server_url,
            "server_type": "mcp-agent-inventory",
            "error_message": f"Cannot connect to mcp-agent-inventory MCP server at {mcp_server_url}. Make sure the server is running."
        }
    except Exception as e:
        return {
            "status": "error",
            "server_url": mcp_server_url,
            "server_type": "mcp-agent-inventory",
            "error_message": f"Error checking server health: {str(e)}"
        }



def get_all_agents_usage(mcp_server_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Get usage statistics for ALL local agents from the mcp-agent-inventory MCP server.
    
    Args:
        mcp_server_url: URL of the AgentInventory MCP server (optional)
        
    Returns:
        dict: Dictionary containing usage statistics for all agents
    """
    if not mcp_server_url:
        mcp_server_url = MCP_AGENT_INVENTORY_URL
        
    try:
        # First list all agents
        list_endpoint = f"{mcp_server_url}/local/agents"
        resp = requests.get(list_endpoint, timeout=10)
        resp.raise_for_status()
        agents = resp.json().get("agents", [])
        
        results = []
        for agent in agents:
            agent_id = agent.get("id")
            # Get usage for each
            usage_endpoint = f"{mcp_server_url}/local/agents/{agent_id}/usage"
            try:
                u_resp = requests.get(usage_endpoint, timeout=5)
                if u_resp.status_code == 200:
                    u_data = u_resp.json()
                    results.append({
                        "agent_id": agent_id,
                        "description": agent.get("description"),
                        "usage": u_data
                    })
            except Exception:
                continue
                
        return {
            "status": "success",
            "agents_usage": results,
            "count": len(results)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error getting all agents usage: {str(e)}"
        }

# Create the AI Agent using Google ADK
root_agent = Agent(
    name="MetricsAgent",
    model=AGENT_MODEL,  # From global config (default: gemini-2.5-flash-lite)
    description="An AI agent that retrieves and analyzes agent usage statistics and metrics from the mcp-agent-inventory MCP server. Specializes in querying agent performance metrics including usage patterns, latency, and failure rates for both local and deployed (GCP Reasoning Engine) agents.",
    instruction=""" 
    You are a MetricsAgent that specializes in retrieving and analyzing agent usage statistics and metrics from the mcp-agent-inventory MCP server.
    
    The mcp-agent-inventory MCP server provides:
    - Local agents: Agents running locally with in-memory inventory
    - Deployed agents: Agents deployed to GCP Vertex AI Reasoning Engine
    
    Your capabilities include:
    1. Retrieving usage statistics for specific agents (local or deployed)
    2. Listing all available agents in the inventory (local and/or deployed)
    3. Retrieving usage statistics for ALL agents in one batch
    4. Analyzing agent performance metrics including:
       - Total runs and failure counts
       - Average input/output tokens
       - Latency percentiles (p50, p95)
       - Success rates
    5. Providing insights about agent performance and identifying bottlenecks
    
    When users ask about agent usage:
    1. Use the get_agent_usage tool to query the mcp-agent-inventory MCP server for a specific agent
    2. Use the get_all_agents_usage tool to get a comprehensive report for ALL agents
    3. Present the results clearly, including:
       - Total runs and failures
       - Success rate percentage
       - Average token usage (input and output)
       - Latency metrics (p50, p95)
    4. Provide helpful analysis of the metrics
    
    When users ask to list agents:
    1. Use the list_agents tool to get all available local agents
    2. Use list_agents with include_deployed=True to also get deployed agents
    3. Present the list with descriptions and metadata
    4. Clearly distinguish between local and deployed agents
    
    If the mcp-agent-inventory MCP server is not available:
    1. Use the check_agent_inventory_health tool to diagnose the issue
    2. Provide helpful guidance on how to start the server
    3. Suggest alternative approaches if possible
    
    Always be helpful, clear, and concise. Format statistics in a readable way with proper units.
    """,
    tools=[get_agent_usage, get_all_agents_usage, list_agents, check_agent_inventory_health]
)


if __name__ == "__main__":
    # Example usage
    print("MetricsAgent")
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

