"""
AI Agent with MCP Server Integration
Uses Google ADK to create an agent that can query token statistics via MCP server
"""

from google.adk.agents import Agent
import vertexai
import os
import sys
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from datetime import datetime
import time

# Add parent directory to path to import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from config import AGENT_MODEL, MCP_TOKENSTATS_URL

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
    # Get MCP server URL from config
    mcp_server_url = MCP_TOKENSTATS_URL
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


def calculate_token_cost_from_counts(
    input_tokens: int, 
    output_tokens: int, 
    model: str = "gemini-2.5-flash"
) -> Dict[str, Any]:
    """
    Calculate token cost from known token counts using mcp-tokenstats server.
    
    This function calculates the actual cost based on input and output token counts
    without needing the full prompt text. It calls the mcp-tokenstats server to get
    pricing information and calculates the cost.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name (default: "gemini-2.5-flash")
    
    Returns:
        dict: Dictionary containing cost breakdown:
            - status: "success" or "error"
            - input_tokens: Number of input tokens
            - output_tokens: Number of output tokens
            - total_tokens: Total tokens
            - input_cost_usd: Input cost in USD
            - output_cost_usd: Output cost in USD
            - total_cost_usd: Total cost in USD
            - model: Model name used
            - input_price_per_m: Input price per million tokens
            - output_price_per_m: Output price per million tokens
    """
    mcp_server_url = os.environ.get("MCP_TOKENSTATS_URL", "http://localhost:8000")
    tokenize_endpoint = f"{mcp_server_url}/tokenize"
    
    try:
        # First, get pricing information by making a minimal request
        # We'll use a dummy prompt to get the pricing structure
        response = requests.post(
            tokenize_endpoint,
            json={
                "model": model,
                "prompt": "test",  # Minimal prompt to get pricing info
                "generate": False
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        response.raise_for_status()
        stats = response.json()
        
        # Get pricing from response
        input_price_per_m = stats.get("input_price_per_m", 0.30)  # Default gemini-2.5-flash
        output_price_per_m = stats.get("output_price_per_m", 2.50)
        
        # Calculate cost using the formula: (tokens / 1M) × price_per_m
        input_cost = (input_tokens / 1_000_000) * input_price_per_m
        output_cost = (output_tokens / 1_000_000) * output_price_per_m
        total_cost = input_cost + output_cost
        
        return {
            "status": "success",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "total_cost_usd": round(total_cost, 6),
            "model": model,
            "input_price_per_m": input_price_per_m,
            "output_price_per_m": output_price_per_m,
            "pricing_tier": stats.get("pricing_tier", "standard")
        }
        
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "error_message": f"Cannot connect to MCP TokenStats server at {mcp_server_url}. Make sure the server is running."
        }
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error_message": "Request to MCP TokenStats server timed out. Please try again."
        }
    except requests.exceptions.HTTPError as e:
        return {
            "status": "error",
            "error_message": f"MCP TokenStats server returned error: {e.response.status_code} - {e.response.text}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Unexpected error calculating token cost: {str(e)}"
        }


def check_mcp_server_health() -> Dict[str, Any]:
    """
    Check if the mcp-tokenstats MCP server is running and healthy.
    
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
            "server_type": "mcp-tokenstats",
            "health_check": health_data
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "unhealthy",
            "server_url": mcp_server_url,
            "server_type": "mcp-tokenstats",
            "error_message": f"Cannot connect to mcp-tokenstats MCP server at {mcp_server_url}. Make sure the server is running."
        }
    except Exception as e:
        return {
            "status": "error",
            "server_url": mcp_server_url,
            "server_type": "mcp-tokenstats",
            "error_message": f"Error checking server health: {str(e)}"
        }


# Create the AI Agent using Google ADK
root_agent = Agent(
    name="token_stats_assistant",
    model=AGENT_MODEL,  # From global config (default: gemini-2.5-flash-lite)
    description="An AI assistant that helps analyze token usage statistics using the mcp-tokenstats MCP server. Can estimate token counts, calculate actual costs in USD, and provide insights about text processing requirements.",
    instruction="""
    You are a helpful token statistics assistant powered by the mcp-tokenstats MCP server.
    
    The mcp-tokenstats MCP server provides:
    - Token counting using Gemini API
    - Cost calculation based on official Gemini API pricing
    - Support for multiple models (gemini-2.5-pro, gemini-2.5-flash, gemini-1.5-pro, etc.)
    - Real-time cost breakdown (input cost + output cost = total cost)
    
    Your capabilities include:
    1. Analyzing text prompts to estimate token usage
    2. Calculating actual costs in USD for text processing using official pricing
    3. Calculating costs from known token counts (input_tokens and output_tokens)
    4. Providing insights about token limits and compression ratios
    5. Helping users understand token usage for different models
    
    When users ask about token statistics:
    1. Use the get_token_stats tool to query the mcp-tokenstats MCP server
       - Provide the prompt text and model name
       - Set generate=True to get actual token counts and costs from an API call
    2. Present the results clearly, including:
       - Number of input tokens
       - Estimated or actual output tokens
       - Cost breakdown:
         * Input cost (USD): (input_tokens / 1M) × input_price_per_m
         * Output cost (USD): (output_tokens / 1M) × output_price_per_m
         * Total cost (USD): input_cost + output_cost
       - Pricing tier (standard or extended for >200k tokens)
       - Remaining token capacity
       - Compression ratio
    3. Provide helpful context about what these numbers mean
    
    When calculating costs from known token counts:
    1. Use the calculate_token_cost_from_counts tool
       - Provide input_tokens, output_tokens, and model name
    2. This directly calculates cost using the formula: (tokens / 1M) × price_per_m
    3. Returns detailed cost breakdown with pricing information
    
    If the mcp-tokenstats MCP server is not available:
    1. Use the check_mcp_server_health tool to diagnose the issue
    2. Provide helpful guidance on how to start the server
    3. Suggest alternative approaches if possible
    
    Always be helpful, clear, and concise in your responses. Format numbers and costs in a readable way.
    Show the cost formula when helpful: Cost = (input_tokens / 1M) × input_price + (output_tokens / 1M) × output_price
    """,
    tools=[get_token_stats, calculate_token_cost_from_counts, check_mcp_server_health]
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

