"""
MCP Server: ReasoningCost
Remote server for estimating reasoning costs based on chain-of-thought metrics
"""

import json
import os
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import math

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="ReasoningCost MCP Server", version="1.0.0")

# Add CORS middleware for remote access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base constants for cost calculation
# These represent baseline values for "normal" reasoning
BASE_TOKENS = 500  # Baseline token count for standard reasoning
BASE_STEPS = 5  # Baseline number of reasoning steps
BASE_TOOL_CALLS = 1  # Baseline number of tool calls


class Trace(BaseModel):
    """Model for reasoning trace"""
    steps: int
    tool_calls: int
    tokens_in_trace: int


class EstimateRequest(BaseModel):
    """Request model for estimate endpoint"""
    trace: Trace


class EstimateResponse(BaseModel):
    """Response model for estimate endpoint"""
    reasoning_depth: int
    tool_invocations: int
    expansion_factor: float
    cost_score: float


def calculate_expansion_factor(tokens_in_trace: int, steps: int) -> float:
    """
    Calculate the expansion factor (how much the prompt grew)
    
    Expansion factor measures prompt length growth relative to base reasoning.
    Higher values indicate more verbose reasoning.
    
    Args:
        tokens_in_trace: Total tokens in the reasoning trace
        steps: Number of reasoning steps
        
    Returns:
        float: Expansion factor (typically 1.0-3.0)
    """
    if steps == 0:
        return 1.0
    
    # Calculate expected tokens for this many steps
    # Each step typically adds ~100-200 tokens
    expected_tokens_per_step = BASE_TOKENS / BASE_STEPS
    expected_tokens = steps * expected_tokens_per_step
    
    if expected_tokens == 0:
        return 1.0
    
    # Expansion factor is ratio of actual to expected tokens
    expansion = tokens_in_trace / expected_tokens
    
    # Normalize to reasonable range (1.0-3.0 typically)
    # Cap at 3.0 to avoid extreme values
    return min(round(expansion, 2), 3.0)


def calculate_cost_score(
    steps: int,
    tool_calls: int,
    tokens_in_trace: int,
    expansion_factor: float
) -> float:
    """
    Calculate a cost score (0.0-1.0+) representing reasoning cost
    
    The score combines multiple factors:
    - Reasoning depth (more steps = higher cost)
    - Tool invocations (each tool call adds overhead)
    - Token expansion (more verbose reasoning = higher cost)
    
    Args:
        steps: Number of reasoning steps
        tool_calls: Number of tool invocations
        tokens_in_trace: Total tokens in trace
        expansion_factor: Token expansion factor
        
    Returns:
        float: Cost score (0.0 = minimal cost, 1.0+ = expensive)
    """
    # Normalize steps (0-20 range maps to 0-0.4 score)
    steps_score = min(steps / 20.0, 1.0) * 0.4
    
    # Normalize tool calls (0-10 range maps to 0-0.3 score)
    tool_score = min(tool_calls / 10.0, 1.0) * 0.3
    
    # Expansion factor contributes (1.0-3.0 maps to 0-0.3 score)
    expansion_score = min((expansion_factor - 1.0) / 2.0, 1.0) * 0.3
    
    # Combine scores
    total_score = steps_score + tool_score + expansion_score
    
    # Round to 2 decimal places
    return round(total_score, 2)


@app.post("/estimate", response_model=EstimateResponse)
async def estimate_reasoning_cost(request: EstimateRequest) -> EstimateResponse:
    """
    Estimate reasoning cost based on trace metrics
    
    This endpoint analyzes reasoning traces to detect:
    - Runaway chain-of-thought (high steps, high expansion)
    - Expensive reasoning paths (high tool calls, high tokens)
    - Opportunities for reasoning compression
    
    Args:
        request: EstimateRequest containing trace metrics
        
    Returns:
        EstimateResponse with cost analysis
    """
    try:
        trace = request.trace
        
        # Validate inputs
        if trace.steps < 0:
            raise HTTPException(status_code=400, detail="Steps must be non-negative")
        if trace.tool_calls < 0:
            raise HTTPException(status_code=400, detail="Tool calls must be non-negative")
        if trace.tokens_in_trace < 0:
            raise HTTPException(status_code=400, detail="Tokens in trace must be non-negative")
        
        # Calculate metrics
        reasoning_depth = trace.steps
        tool_invocations = trace.tool_calls
        expansion_factor = calculate_expansion_factor(trace.tokens_in_trace, trace.steps)
        cost_score = calculate_cost_score(
            trace.steps,
            trace.tool_calls,
            trace.tokens_in_trace,
            expansion_factor
        )
        
        return EstimateResponse(
            reasoning_depth=reasoning_depth,
            tool_invocations=tool_invocations,
            expansion_factor=expansion_factor,
            cost_score=cost_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error estimating reasoning cost: {str(e)}")


@app.post("/estimate_multiple")
async def estimate_multiple_traces(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Estimate reasoning cost for multiple traces (batch processing)
    
    Args:
        request: Dictionary with "traces" key containing list of traces
        
    Returns:
        Dictionary with list of estimates
    """
    try:
        traces = request.get("traces", [])
        
        if not isinstance(traces, list):
            raise HTTPException(status_code=400, detail="Traces must be a list")
        
        estimates = []
        for trace_data in traces:
            trace = Trace(**trace_data)
            estimate_request = EstimateRequest(trace=trace)
            estimate = await estimate_reasoning_cost(estimate_request)
            estimates.append(estimate.dict())
        
        return {
            "estimates": estimates,
            "count": len(estimates)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error estimating multiple traces: {str(e)}")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "ReasoningCost MCP Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "estimate": "POST /estimate",
            "estimate_multiple": "POST /estimate_multiple",
        },
        "description": "Estimates reasoning costs based on chain-of-thought metrics",
        "use_cases": [
            "Detecting runaway chain-of-thought",
            "Penalizing expensive reasoning paths",
            "Evaluating reasoning compression strategies"
        ]
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

