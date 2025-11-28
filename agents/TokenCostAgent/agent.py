"""
TokenCostAgent
Uses Google ADK to create an agent that can query token statistics and calculate costs using Vertex AI directly.
"""

from google.adk.agents import Agent
import vertexai
from vertexai.generative_models import GenerativeModel
import os
import sys
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Add parent directory to path to import config
# Add parent directory to path to import config
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)
from config import AGENT_MODEL

# Load environment variables from shared .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Initialize Vertex AI
vertexai.init(
    project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)

# Pricing table (USD per 1M tokens)
# Based on public pricing as of late 2024/early 2025
PRICING_TABLE = {
    "gemini-1.5-pro": {"input": 3.50, "output": 10.50},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.0-pro": {"input": 0.50, "output": 1.50},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.5-flash": {"input": 0.10, "output": 0.40}, # Estimated/Placeholder
    "gemini-2.5-pro": {"input": 4.00, "output": 12.00}, # Estimated/Placeholder
}

def get_token_stats(prompt: str, model_name: str = "gemini-1.5-flash") -> Dict[str, Any]:
    """
    Get token usage statistics using Vertex AI.
    
    Args:
        prompt: The text prompt to analyze
        model_name: The model name (default: "gemini-1.5-flash")
    
    Returns:
        dict: Token statistics and cost estimates
    """
    try:
        # Use Vertex AI to count tokens
        model = GenerativeModel(model_name)
        response = model.count_tokens(prompt)
        input_tokens = response.total_tokens
        
        # Get pricing
        pricing = PRICING_TABLE.get(model_name)
        if not pricing:
            # Fallback to flash pricing if model not found
            pricing = PRICING_TABLE["gemini-1.5-flash"]
            pricing_note = f"Model {model_name} not found in pricing table, using gemini-1.5-flash rates."
        else:
            pricing_note = ""
            
        # Calculate input cost
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        
        return {
            "status": "success",
            "input_tokens": input_tokens,
            "estimated_cost_usd": round(input_cost, 6),
            "model": model_name,
            "pricing_used": pricing,
            "note": pricing_note
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error counting tokens with Vertex AI: {str(e)}"
        }

def calculate_token_cost_from_counts(
    input_tokens: int, 
    output_tokens: int, 
    model_name: str = "gemini-1.5-flash"
) -> Dict[str, Any]:
    """
    Calculate cost from known token counts using local pricing table.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model_name: Model name (default: "gemini-1.5-flash")
    
    Returns:
        dict: Cost breakdown
    """
    pricing = PRICING_TABLE.get(model_name)
    if not pricing:
        pricing = PRICING_TABLE["gemini-1.5-flash"]
        note = f"Model {model_name} not found in pricing table, using gemini-1.5-flash rates."
    else:
        note = ""

    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    total_cost = input_cost + output_cost
    
    return {
        "status": "success",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(total_cost, 6),
        "model": model_name,
        "input_price_per_m": pricing["input"],
        "output_price_per_m": pricing["output"],
        "note": note
    }

def check_vertex_ai_health() -> Dict[str, Any]:
    """
    Check if Vertex AI connection is working.
    
    Returns:
        dict: Health status
    """
    try:
        model = GenerativeModel("gemini-1.5-flash")
        # Simple token count check
        model.count_tokens("test")
        return {
            "status": "healthy",
            "service": "Vertex AI",
            "project": os.environ.get("GOOGLE_CLOUD_PROJECT")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "Vertex AI",
            "error_message": str(e)
        }

# Create the AI Agent using Google ADK
root_agent = Agent(
    name="TokenCostAgent",
    model=AGENT_MODEL,  # From global config
    description="An AI agent that analyzes token usage statistics and calculates costs using Vertex AI directly. Can estimate token counts and calculate actual costs in USD.",
    instruction="""
    You are a TokenCostAgent that helps analyze token usage statistics and calculate costs.
    
    You use the Vertex AI SDK directly to count tokens and a local pricing table to estimate costs.
    You do NOT need an external MCP server for this.
    
    Your capabilities include:
    1. Analyzing text prompts to estimate token usage (using Vertex AI)
    2. Calculating actual costs in USD for text processing using official pricing
    3. Calculating costs from known token counts (input_tokens and output_tokens)
    
    When users ask about token statistics:
    1. Use the get_token_stats tool
       - Provide the prompt text and model name
    2. Present the results clearly, including:
       - Number of input tokens
       - Estimated cost (USD)
       - Model used
    
    When calculating costs from known token counts:
    1. Use the calculate_token_cost_from_counts tool
       - Provide input_tokens, output_tokens, and model name
    2. Returns detailed cost breakdown with pricing information
    
    If Vertex AI is not available:
    1. Use the check_vertex_ai_health tool to diagnose the issue
    
    Always be helpful, clear, and concise in your responses. Format numbers and costs in a readable way.
    """,
    tools=[get_token_stats, calculate_token_cost_from_counts, check_vertex_ai_health]
)

if __name__ == "__main__":
    # Example usage
    print("TokenCostAgent (Local Mode)")
    print("=" * 50)
    print()
    
    # Check health
    print("Checking Vertex AI health...")
    health = check_vertex_ai_health()
    print(f"Status: {health.get('status')}")
    if health.get('error_message'):
        print(f"Error: {health.get('error_message')}")
    print()
    
    # Example query
    if health.get("status") == "healthy":
        print("Example: Getting token stats for a sample prompt...")
        result = root_agent.run("Analyze the token usage for this text: 'The quick brown fox jumps over the lazy dog.'")
        print(result)
