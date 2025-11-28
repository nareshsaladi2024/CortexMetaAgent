# Refactoring: Agent Inventory Delegation

## Summary

Removed direct MCP server calls to `list_agents_from_inventory` and replaced them with delegation through MetricsAgent, following the CortexMetaAgent architecture pattern.

## Changes Made

### 1. AutoEvalAgent (`agents/AutoEvalAgent/agent.py`)

**Before:**
- `list_agents_from_inventory()` made direct HTTP requests to MCP server
- Direct dependency on MCP server URL and endpoints

**After:**
- `list_agents_from_inventory()` now delegates to MetricsAgent's `list_agents()` function
- Imports `list_agents` from `agents.MetricsAgent.agent`
- Maintains same function signature for backward compatibility
- Updated documentation to reflect delegation pattern

**Key Changes:**
```python
# Added import
from agents.MetricsAgent.agent import list_agents as metrics_list_agents

# Function now delegates instead of direct HTTP call
def list_agents_from_inventory(mcp_server_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Delegates to MetricsAgent through CortexMetaAgent architecture.
    MetricsAgent handles all MCP server interactions for agent inventory.
    """
    result = metrics_list_agents(mcp_server_url=mcp_server_url, include_deployed=False)
    # ... format and return result
```

### 2. Orchestrator (`workflow/orchestrator.py`)

**Before:**
- Imported `list_agents_from_inventory` from AutoEvalAgent
- Used it directly in `detect_agent_changes()`

**After:**
- Imports `list_agents` from MetricsAgent (preferred)
- Falls back to AutoEvalAgent's delegation function if MetricsAgent unavailable
- Updated `detect_agent_changes()` to use MetricsAgent first

**Key Changes:**
```python
# Added import
from agents.MetricsAgent.agent import list_agents as metrics_list_agents

# Updated detect_agent_changes()
if metrics_list_agents is not None:
    # Delegate to MetricsAgent (preferred)
    current_agents = metrics_list_agents(include_deployed=False)
elif list_agents_from_inventory is not None:
    # Fallback to AutoEvalAgent's delegation function
    current_agents = list_agents_from_inventory()
```

## Architecture Benefits

1. **Separation of Concerns**: MetricsAgent is the single source of truth for agent inventory queries
2. **Consistency**: All agent inventory operations go through MetricsAgent
3. **Maintainability**: MCP server changes only need to be updated in MetricsAgent
4. **Testability**: Easier to mock and test delegation functions
5. **Backward Compatibility**: Function signatures remain the same, existing code continues to work

## Call Flow

**Before:**
```
AutoEvalAgent → Direct HTTP → MCP Server (AgentInventory)
```

**After:**
```
AutoEvalAgent → MetricsAgent → MCP Server (AgentInventory)
     ↓
CortexMetaAgent orchestrates MetricsAgent
```

## Files Modified

1. `CortexMetaAgent/agents/AutoEvalAgent/agent.py`
   - Removed direct MCP HTTP calls
   - Added MetricsAgent import
   - Updated `list_agents_from_inventory()` to delegate
   - Updated documentation strings

2. `CortexMetaAgent/workflow/orchestrator.py`
   - Added MetricsAgent import
   - Updated `detect_agent_changes()` to prefer MetricsAgent
   - Added fallback logic

## Testing

The function `list_agents_from_inventory()` maintains the same signature and return format, so:
- Existing code using this function continues to work
- Test files (`test-agent.py`) require no changes
- The delegation is transparent to callers

## Next Steps

- Consider removing `list_agents_from_inventory` from AutoEvalAgent tools if not needed
- Update any other direct MCP calls to follow the same delegation pattern
- Document the delegation pattern in architecture documentation

