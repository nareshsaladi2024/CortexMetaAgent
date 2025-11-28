
import sys
import os
from unittest.mock import MagicMock, patch
import json

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.TokenCostAgent.agent import root_agent

def test_cost_report():
    print("Testing get_agent_cost_report...")
    
    # Get the tool function
    tool_name = "get_agent_cost_report"
    tool_func = next((t for t in root_agent.tools if t.__name__ == tool_name), None)
    
    if not tool_func:
        print(f"Error: Tool {tool_name} not found in agent tools.")
        return

    # Mock responses
    mock_local_agents = {
        "agents": [
            {"id": "agent1", "description": "Test Agent 1"}
        ]
    }
    
    mock_usage = {
        "total_runs": 10,
        "avg_input_tokens": 100,
        "avg_output_tokens": 50
    }
    
    mock_deployed_agents = {
        "agents": [
            {"agent_id": "deployed1", "display_name": "Deployed Agent 1"}
        ]
    }
    
    mock_deployed_usage = {
        "requests_last_hour": 5
    }

    # Patch requests.get
    with patch('requests.get') as mock_get:
        def side_effect(url, timeout=5):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            
            if "/local/agents/agent1/usage" in url:
                mock_resp.json.return_value = mock_usage
            elif "/local/agents" in url:
                mock_resp.json.return_value = mock_local_agents
            elif "/deployed/agents/deployed1/usage" in url:
                mock_resp.json.return_value = mock_deployed_usage
            elif "/deployed/agents" in url:
                mock_resp.json.return_value = mock_deployed_agents
            else:
                mock_resp.status_code = 404
                
            return mock_resp
            
        mock_get.side_effect = side_effect
        
        # Run the tool
        report = tool_func(mcp_inventory_url="http://mock-server")
        
        print("Report:", json.dumps(report, indent=2))
        
        # Verify
        assert len(report["local_agents"]) == 1
        assert report["local_agents"][0]["agent_id"] == "agent1"
        assert report["local_agents"][0]["total_input_tokens"] == 1000  # 10 * 100
        assert report["local_agents"][0]["total_output_tokens"] == 500  # 10 * 50
        assert report["total_estimated_cost_usd"] > 0
        
        assert len(report["deployed_agents"]) == 1
        assert report["deployed_agents"][0]["agent_id"] == "deployed1"
        
        print("Test passed!")

if __name__ == "__main__":
    test_cost_report()
