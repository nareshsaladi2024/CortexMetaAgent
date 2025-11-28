"""
TokenCostAgent
Uses Google ADK to create an agent that can query token statistics and calculate costs using Vertex AI directly.
"""

from google.adk.agents import Agent
import vertexai
from vertexai.generative_models import GenerativeModel
import os
import sys
from typing import Dict, Any, Optional, List
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


def calculate_cost_from_response_metadata(
    metadata: Dict[str, Any],
    model_name: str = "gemini-1.5-flash"
) -> Dict[str, Any]:
    """
    Calculate cost from LLM response metadata (e.g., from GenerateContentResponse).
    
    Args:
        metadata: Dictionary containing token counts. Supports keys:
                 - prompt_token_count / candidates_token_count
                 - input_tokens / output_tokens
        model_name: Model name (default: "gemini-1.5-flash")
        
    Returns:
        dict: Cost breakdown
    """
    # Extract token counts handling different formats
    input_tokens = metadata.get("prompt_token_count") or metadata.get("input_tokens") or 0
    output_tokens = metadata.get("candidates_token_count") or metadata.get("output_tokens") or 0
    
    return calculate_token_cost_from_counts(
        input_tokens=int(input_tokens),
        output_tokens=int(output_tokens),
        model_name=model_name
    )


def calculate_batch_agent_cost(agents_usage: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate costs for a batch of agents based on provided usage data.
    
    Args:
        agents_usage: List of agent usage dictionaries (from MetricsAgent)
        
    Returns:
        dict: Cost report
    """
    report = {
        "status": "success",
        "local_agents": [],
        "total_estimated_cost_usd": 0.0
    }
    
    for agent_data in agents_usage:
        # Handle different structures (direct usage dict or wrapper)
        usage = agent_data.get("usage", agent_data)
        agent_id = agent_data.get("agent_id", usage.get("agent_id", "unknown"))
        
        total_runs = usage.get("total_runs", 0)
        avg_input = usage.get("avg_input_tokens", 0)
        avg_output = usage.get("avg_output_tokens", 0)
        
        total_input = total_runs * avg_input
        total_output = total_runs * avg_output
        
        # Estimate using default pricing (gemini-1.5-flash)
        cost_est = calculate_token_cost_from_counts(
            int(total_input), int(total_output), "gemini-1.5-flash"
        )
        
        agent_cost = {
            "agent_id": agent_id,
            "total_runs": total_runs,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "estimated_total_cost_usd": cost_est["total_cost_usd"]
        }
        report["local_agents"].append(agent_cost)
        report["total_estimated_cost_usd"] += cost_est["total_cost_usd"]
        
    return report

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
        4. Calculating costs directly from LLM response metadata
        5. Calculating costs for a batch of agents using provided usage data (from MetricsAgent)
        
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
        
        When you have raw metadata from an LLM call:
        1. Use the calculate_cost_from_response_metadata tool
           - Provide the metadata dictionary and model name
           
        When provided with a list of agent usage data (e.g. from MetricsAgent):
        1. Use the calculate_batch_agent_cost tool
        2. Summarize the costs for the provided agents
        
        If Vertex AI is not available:
        1. Use the check_vertex_ai_health tool to diagnose the issue
        
        Always be helpful, clear, and concise in your responses. Format numbers and costs in a readable way.
        """,
        tools=[get_token_stats, calculate_token_cost_from_counts, calculate_cost_from_response_metadata, calculate_batch_agent_cost, check_vertex_ai_health]
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
