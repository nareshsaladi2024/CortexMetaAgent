"""
MCP Server: AgentInventory
Remote server for tracking agent metadata, usage, and performance metrics
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import statistics

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="AgentInventory MCP Server", version="1.0.0")

# Add CORS middleware for remote access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for agent metadata
# Format: {agent_id: {id, description, ...}}
agent_metadata: Dict[str, Dict[str, Any]] = {}

# Storage for execution records
# Format: {agent_id: [execution_record, ...]}
execution_records: Dict[str, List[Dict[str, Any]]] = {}


class AgentExecution(BaseModel):
    """Model for recording an agent execution"""
    agent_id: str
    execution_id: Optional[str] = None
    timestamp: Optional[str] = None
    success: bool = True
    runtime_ms: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    error_message: Optional[str] = None


class AgentMetadata(BaseModel):
    """Model for agent metadata"""
    id: str
    description: str
    avg_cost: Optional[float] = None
    avg_latency: Optional[float] = None


class ListAgentsResponse(BaseModel):
    """Response model for list_agents endpoint"""
    agents: List[Dict[str, Any]]


class AgentUsageResponse(BaseModel):
    """Response model for usage endpoint"""
    total_runs: int
    failures: int
    avg_input_tokens: float
    avg_output_tokens: float
    p50_latency_ms: float
    p95_latency_ms: float


def calculate_percentile(data: List[float], percentile: float) -> float:
    """
    Calculate percentile from a list of values
    
    Args:
        data: List of numeric values
        percentile: Percentile to calculate (0-100)
        
    Returns:
        float: Percentile value
    """
    if not data:
        return 0.0
    
    sorted_data = sorted(data)
    index = (percentile / 100.0) * (len(sorted_data) - 1)
    
    if index.is_integer():
        return sorted_data[int(index)]
    else:
        lower = sorted_data[int(index)]
        upper = sorted_data[int(index) + 1]
        return lower + (upper - lower) * (index - int(index))


def record_execution(execution: AgentExecution) -> None:
    """
    Record an agent execution in the inventory
    
    Args:
        execution: AgentExecution object with execution details
    """
    agent_id = execution.agent_id
    
    # Initialize agent if not exists
    if agent_id not in agent_metadata:
        agent_metadata[agent_id] = {
            "id": agent_id,
            "description": f"Agent {agent_id}",
        }
    
    if agent_id not in execution_records:
        execution_records[agent_id] = []
    
    # Create execution record
    execution_data = {
        "execution_id": execution.execution_id or f"{agent_id}_{datetime.now().timestamp()}",
        "timestamp": execution.timestamp or datetime.now().isoformat(),
        "success": execution.success,
        "runtime_ms": execution.runtime_ms,
        "input_tokens": execution.input_tokens,
        "output_tokens": execution.output_tokens,
        "total_tokens": execution.total_tokens,
        "cost_usd": execution.cost_usd,
        "error_message": execution.error_message,
    }
    
    # Add to records
    execution_records[agent_id].append(execution_data)
    
    # Update agent metadata with averages
    update_agent_averages(agent_id)


def update_agent_averages(agent_id: str) -> None:
    """
    Update agent metadata with average cost and latency
    
    Args:
        agent_id: The ID of the agent
    """
    records = execution_records.get(agent_id, [])
    if not records:
        return
    
    # Calculate average cost
    costs = [r.get("cost_usd") for r in records if r.get("cost_usd") is not None]
    avg_cost = sum(costs) / len(costs) if costs else None
    
    # Calculate average latency
    latencies = [r.get("runtime_ms") for r in records if r.get("runtime_ms") is not None]
    avg_latency = sum(latencies) / len(latencies) if latencies else None
    
    # Update metadata
    if agent_id in agent_metadata:
        if avg_cost is not None:
            agent_metadata[agent_id]["avg_cost"] = round(avg_cost, 6)
        if avg_latency is not None:
            agent_metadata[agent_id]["avg_latency"] = round(avg_latency, 2)


@app.post("/record_execution")
async def record_agent_execution(execution: AgentExecution) -> Dict[str, Any]:
    """
    Record an agent execution in the inventory
    
    Args:
        execution: AgentExecution object with execution details
        
    Returns:
        dict: Confirmation of recorded execution
    """
    try:
        record_execution(execution)
        return {
            "status": "success",
            "message": f"Execution recorded for agent {execution.agent_id}",
            "execution_id": execution.execution_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording execution: {str(e)}")


@app.post("/register_agent")
async def register_agent(metadata: AgentMetadata) -> Dict[str, Any]:
    """
    Register or update agent metadata
    
    Args:
        metadata: AgentMetadata object with agent information
        
    Returns:
        dict: Confirmation of registration
    """
    try:
        agent_metadata[metadata.id] = {
            "id": metadata.id,
            "description": metadata.description,
            "avg_cost": metadata.avg_cost,
            "avg_latency": metadata.avg_latency,
        }
        
        # Update averages from execution records if available
        update_agent_averages(metadata.id)
        
        return {
            "status": "success",
            "message": f"Agent {metadata.id} registered/updated"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering agent: {str(e)}")


@app.get("/list_agents", response_model=ListAgentsResponse)
async def list_agents() -> ListAgentsResponse:
    """
    List all agents in the inventory with their metadata
    
    Returns:
        ListAgentsResponse: List of all agents with metadata
    """
    try:
        agents_list = []
        
        for agent_id, metadata in agent_metadata.items():
            # Ensure averages are up to date
            update_agent_averages(agent_id)
            
            agent_info = {
                "id": metadata.get("id", agent_id),
                "description": metadata.get("description", f"Agent {agent_id}"),
                "avg_cost": metadata.get("avg_cost"),
                "avg_latency": metadata.get("avg_latency"),
            }
            agents_list.append(agent_info)
        
        # Sort by agent ID
        agents_list.sort(key=lambda x: x["id"])
        
        return ListAgentsResponse(agents=agents_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing agents: {str(e)}")


@app.get("/usage", response_model=AgentUsageResponse)
async def get_agent_usage(agent: str = Query(..., description="Agent ID to get usage for")) -> AgentUsageResponse:
    """
    Get detailed usage statistics for a specific agent
    
    Args:
        agent: The ID of the agent (query parameter)
        
    Returns:
        AgentUsageResponse: Detailed usage statistics
    """
    try:
        agent_id = agent
        
        if agent_id not in agent_metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Agent {agent_id} not found in inventory"
            )
        
        records = execution_records.get(agent_id, [])
        
        if not records:
            return AgentUsageResponse(
                total_runs=0,
                failures=0,
                avg_input_tokens=0.0,
                avg_output_tokens=0.0,
                p50_latency_ms=0.0,
                p95_latency_ms=0.0,
            )
        
        # Calculate statistics
        total_runs = len(records)
        failures = sum(1 for r in records if not r.get("success", False))
        
        # Average input tokens
        input_tokens_list = [r.get("input_tokens", 0) for r in records if r.get("input_tokens") is not None]
        avg_input_tokens = sum(input_tokens_list) / len(input_tokens_list) if input_tokens_list else 0.0
        
        # Average output tokens
        output_tokens_list = [r.get("output_tokens", 0) for r in records if r.get("output_tokens") is not None]
        avg_output_tokens = sum(output_tokens_list) / len(output_tokens_list) if output_tokens_list else 0.0
        
        # Latency percentiles
        latencies = [r.get("runtime_ms") for r in records if r.get("runtime_ms") is not None]
        p50_latency_ms = calculate_percentile(latencies, 50) if latencies else 0.0
        p95_latency_ms = calculate_percentile(latencies, 95) if latencies else 0.0
        
        return AgentUsageResponse(
            total_runs=total_runs,
            failures=failures,
            avg_input_tokens=round(avg_input_tokens, 2),
            avg_output_tokens=round(avg_output_tokens, 2),
            p50_latency_ms=round(p50_latency_ms, 2),
            p95_latency_ms=round(p95_latency_ms, 2),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting agent usage: {str(e)}")


@app.delete("/agent/{agent_id}")
async def delete_agent(agent_id: str) -> Dict[str, Any]:
    """
    Delete an agent and all its execution records from the inventory
    
    Args:
        agent_id: The ID of the agent to delete
        
    Returns:
        dict: Confirmation of deletion
    """
    try:
        if agent_id not in agent_metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Agent {agent_id} not found in inventory"
            )
        
        del agent_metadata[agent_id]
        if agent_id in execution_records:
            del execution_records[agent_id]
        
        return {
            "status": "success",
            "message": f"Agent {agent_id} and all its records deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting agent: {str(e)}")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "AgentInventory MCP Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "list_agents": "GET /list_agents",
            "usage": "GET /usage?agent={agent_id}",
            "record_execution": "POST /record_execution",
            "register_agent": "POST /register_agent",
            "delete_agent": "DELETE /agent/{agent_id}",
        },
        "agent_count": len(agent_metadata),
        "total_executions": sum(len(records) for records in execution_records.values()),
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
