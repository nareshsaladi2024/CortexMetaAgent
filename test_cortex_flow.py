
import sys
import os
from unittest.mock import MagicMock, patch
import json

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.MetricsAgent.agent import root_agent as metrics_agent
from agents.TokenCostAgent.agent import root_agent as token_cost_agent

def test_flow():
    print("Testing Metrics -> TokenCost flow...")
    
    # 1. Mock MetricsAgent getting data
    print("\nStep 1: MetricsAgent.get_all_agents_usage")
    metrics_tool = next(t for t in metrics_agent.tools if t.__name__ == "get_all_agents_usage")
    
    # Mock response from MCP server
    mock_list_resp = {
        "agents": [
            {"id": "agent1", "description": "Test Agent 1"},
            {"id": "agent2", "description": "Test Agent 2"}
        ]
    }
    
    mock_usage_1 = {
        "total_runs": 100,
        "avg_input_tokens": 500,
        "avg_output_tokens": 100
    }
    
    mock_usage_2 = {
        "total_runs": 50,
        "avg_input_tokens": 200,
        "avg_output_tokens": 50
    }
    
    with patch('requests.get') as mock_get:
        def side_effect(url, timeout=10):
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            
            if "/local/agents/agent1/usage" in url:
                mock_resp.json.return_value = mock_usage_1
            elif "/local/agents/agent2/usage" in url:
                mock_resp.json.return_value = mock_usage_2
            elif "/local/agents" in url:
                mock_resp.json.return_value = mock_list_resp
            else:
                mock_resp.status_code = 404
            return mock_resp
            
        mock_get.side_effect = side_effect
        
        # Run Metrics tool
        metrics_result = metrics_tool(mcp_server_url="http://mock")
        print(f"Metrics Result: Found {metrics_result['count']} agents")
        
        # 2. Pass data to TokenCostAgent
        print("\nStep 2: TokenCostAgent.calculate_batch_agent_cost")
        token_tool = next(t for t in token_cost_agent.tools if t.__name__ == "calculate_batch_agent_cost")
        
        # Pass the 'agents_usage' list from metrics result
        cost_result = token_tool(metrics_result['agents_usage'])
        
        print("Cost Result Summary:")
        print(f"Total Estimated Cost: ${cost_result['total_estimated_cost_usd']:.4f}")
        for agent in cost_result['local_agents']:
            print(f"- {agent['agent_id']}: ${agent['estimated_total_cost_usd']:.4f}")
            
        # Verify calculations
        # Agent 1: 100 runs * (500 in + 100 out)
        # Input: 50,000 tokens * $0.075/1M = $0.00375
        # Output: 10,000 tokens * $0.30/1M = $0.00300
        # Total: $0.00675
        
        agent1 = next(a for a in cost_result['local_agents'] if a['agent_id'] == "agent1")
        print(f"\nVerification for Agent 1: Expected ~$0.00675, Got ${agent1['estimated_total_cost_usd']:.5f}")
        
        assert len(cost_result['local_agents']) == 2
        assert cost_result['total_estimated_cost_usd'] > 0

if __name__ == "__main__":
    test_flow()
