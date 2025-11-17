"""
AI Agent with MCP Server Integration
Uses Google ADK to create an agent that can query token statistics via MCP server
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


def get_token_stats(prompt: str, model: str = "gemini-2.5-flash") -> Dict[str, Any]:
    """
    Get token usage statistics from the MCP TokenStats server.
    
    This tool queries the remote MCP server to get token counts, cost estimates,
    and other statistics for a given prompt and model.
    
    Args:
        prompt: The text prompt to analyze for token usage
        model: The model name (default: "gemini-2.5-flash")
    
    Returns:
        dict: Dictionary containing token statistics including:
            - input_tokens: Number of input tokens
            - estimated_output_tokens: Estimated output tokens
            - estimated_cost_usd: Estimated cost in USD
            - max_tokens_remaining: Maximum tokens remaining
            - compression_ratio: Compression ratio
    """
    # Get MCP server URL from environment or use default
    mcp_server_url = os.environ.get("MCP_TOKENSTATS_URL", "http://localhost:8000")
    tokenize_endpoint = f"{mcp_server_url}/tokenize"
    
    try:
        # Make request to MCP server
        response = requests.post(
            tokenize_endpoint,
            json={
                "model": model,
                "prompt": prompt
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Raise exception if request failed
        response.raise_for_status()
        
        # Return token statistics
        stats = response.json()
        return {
            "status": "success",
            "input_tokens": stats.get("input_tokens", 0),
            "estimated_output_tokens": stats.get("estimated_output_tokens", 0),
            "estimated_cost_usd": stats.get("estimated_cost_usd", 0.0),
            "max_tokens_remaining": stats.get("max_tokens_remaining", 0),
            "compression_ratio": stats.get("compression_ratio", 0.0),
            "model": model
        }
        
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "error_message": f"Cannot connect to MCP server at {mcp_server_url}. Make sure the server is running."
        }
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_message": "Request to MCP server timed out. Please try again."
        }
    except requests.exceptions.HTTPError as e:
        return {
            "status": "error",
            "error_message": f"MCP server returned error: {e.response.status_code} - {e.response.text}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error: {str(e)}"
        }


def check_mcp_server_health() -> Dict[str, Any]:
    """
    Check if the MCP TokenStats server is running and healthy.
    
    Returns:
        dict: Dictionary containing server health status
    """
    mcp_server_url = os.environ.get("MCP_TOKENSTATS_URL", "http://localhost:8000")
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
            "error_message": f"Cannot connect to MCP server at {mcp_server_url}. Make sure the server is running."
        }
    except Exception as e:
        return {
            "status": "error",
            "server_url": mcp_server_url,
            "error_message": f"Error checking server health: {str(e)}"
        }


# Create the AI Agent using Google ADK
root_agent = Agent(
    name="token_stats_assistant",
    model="gemini-2.5-flash-lite",  # Fast, cost-effective Gemini model
    description="An AI assistant that helps analyze token usage statistics using the MCP TokenStats server. Can estimate token counts, costs, and provide insights about text processing requirements.",
    instruction="""
    You are a helpful token statistics assistant powered by an MCP (Model Control Protocol) server.
    
    Your capabilities include:
    1. Analyzing text prompts to estimate token usage
    2. Calculating estimated costs for text processing
    3. Providing insights about token limits and compression ratios
    4. Helping users understand token usage for different models
    
    When users ask about token statistics:
    1. Use the get_token_stats tool to query the MCP server
    2. Present the results clearly, including:
       - Number of input tokens
       - Estimated output tokens
       - Estimated cost (USD)
       - Remaining token capacity
       - Compression ratio
    3. Provide helpful context about what these numbers mean
    
    If the MCP server is not available:
    1. Use the check_mcp_server_health tool to diagnose the issue
    2. Provide helpful guidance on how to start the server
    3. Suggest alternative approaches if possible
    
    Always be helpful, clear, and concise in your responses. Format numbers and costs in a readable way.
    """,
    tools=[get_token_stats, check_mcp_server_health]
)


if __name__ == "__main__":
    # Example usage
    print("🤖 Token Stats Assistant Agent")
    print("=" * 50)
    print()
    
    # Check server health
    print("Checking MCP server health...")
    health = check_mcp_server_health()
    print(f"Status: {health.get('status')}")
    print()
    
    # Example query
    if health.get("status") == "healthy":
        print("Example: Getting token stats for a sample prompt...")
        result = root_agent.run("Analyze the token usage for this text: 'The quick brown fox jumps over the lazy dog.'")
        print(result)
    else:
        print("⚠️  MCP server is not running. Please start it with:")
        print("   python server.py")
        print("   or")
        print("   .\\run-server.ps1")

