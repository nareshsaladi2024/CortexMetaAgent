"""
MCP Server: TokenStats
Remote server for pulling token usage statistics from Gemini Flash 2.5
"""

import json
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="TokenStats MCP Server", version="1.0.0")

# Add CORS middleware for remote access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

genai.configure(api_key=API_KEY)

# Gemini Flash 2.5 pricing (per million tokens)
# Input: $0.00 (free for now)
# Output: $0.00 (free for now)
# These are approximate values - adjust based on actual pricing
GEMINI_FLASH_2_5_INPUT_COST_PER_MILLION = 0.00  # Update with actual pricing
GEMINI_FLASH_2_5_OUTPUT_COST_PER_MILLION = 0.00  # Update with actual pricing

# Model context limits
MAX_INPUT_TOKENS = 1048576  # 1M tokens for Gemini 2.5 Flash
MAX_OUTPUT_TOKENS = 65536   # 64K tokens for Gemini 2.5 Flash


class TokenizeRequest(BaseModel):
    """Request model for tokenize endpoint"""
    model: str
    prompt: str


class TokenStatsResponse(BaseModel):
    """Response model for token statistics"""
    input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    max_tokens_remaining: int
    compression_ratio: float


def count_tokens_with_gemini(prompt: str, model_name: str = "gemini-2.5-flash") -> Dict[str, Any]:
    """
    Count tokens using Gemini API
    
    Args:
        prompt: The input text to tokenize
        model_name: The Gemini model to use
        
    Returns:
        Dictionary containing token count information
    """
    try:
        # Get the model
        model = genai.GenerativeModel(model_name)
        
        # Count tokens using the API
        result = model.count_tokens(prompt)
        input_tokens = result.total_tokens
        
        # Estimate output tokens (typically 20-50% of input for summaries)
        # Using a conservative estimate of 40% for summary tasks
        estimated_output_tokens = int(input_tokens * 0.4)
        
        # Ensure estimated output doesn't exceed max
        if estimated_output_tokens > MAX_OUTPUT_TOKENS:
            estimated_output_tokens = MAX_OUTPUT_TOKENS
        
        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * GEMINI_FLASH_2_5_INPUT_COST_PER_MILLION
        output_cost = (estimated_output_tokens / 1_000_000) * GEMINI_FLASH_2_5_OUTPUT_COST_PER_MILLION
        total_cost = input_cost + output_cost
        
        # Calculate remaining tokens
        max_tokens_remaining = MAX_INPUT_TOKENS - input_tokens
        
        # Calculate compression ratio (output/input)
        compression_ratio = estimated_output_tokens / input_tokens if input_tokens > 0 else 0
        
        return {
            "input_tokens": input_tokens,
            "estimated_output_tokens": estimated_output_tokens,
            "estimated_cost_usd": round(total_cost, 6),
            "max_tokens_remaining": max_tokens_remaining,
            "compression_ratio": round(compression_ratio, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting tokens: {str(e)}")


@app.post("/tokenize", response_model=TokenStatsResponse)
async def tokenize(request: TokenizeRequest) -> TokenStatsResponse:
    """
    Tokenize endpoint that returns token usage statistics
    
    Args:
        request: TokenizeRequest containing model and prompt
        
    Returns:
        TokenStatsResponse with token statistics
    """
    try:
        # Validate model name
        if "gemini" not in request.model.lower() and "gpt" not in request.model.lower():
            # Default to Gemini for non-specified models
            model_name = "gemini-2.5-flash"
        elif "gemini" in request.model.lower():
            # Extract or map Gemini model name
            if "2.5" in request.model.lower() or "flash" in request.model.lower():
                model_name = "gemini-2.5-flash"
            else:
                model_name = "gemini-2.5-flash"  # Default
        else:
            # For GPT models, we'll use a basic estimation
            # This is a fallback - ideally you'd use OpenAI's tiktoken
            model_name = request.model
        
        # Get token statistics
        stats = count_tokens_with_gemini(request.prompt, model_name)
        
        return TokenStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "TokenStats MCP Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "tokenize": "POST /tokenize"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    try:
        print(f"🚀 Starting TokenStats MCP Server on http://0.0.0.0:{port}")
        print(f"   Press Ctrl+C to stop the server")
        print()
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting server: {e}", file=sys.stderr)
        sys.exit(1)

