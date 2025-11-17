"""
Python script to test the TokenStats MCP Server
"""

import requests
import json
from typing import Dict, Any

SERVER_URL = "http://localhost:8000"
TEST_PROMPT = "Summarize: The quick brown fox jumps over the lazy dog. This is a test of the token counting functionality."


def test_health_check() -> bool:
    """Test the health check endpoint"""
    print("🧪 Test 1: Health Check")
    try:
        response = requests.get(f"{SERVER_URL}/health")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Health check passed: {data.get('status')}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_tokenize(prompt: str, model: str = "gemini-2.5-flash") -> Dict[str, Any]:
    """Test the tokenize endpoint"""
    print(f"\n🧪 Test 2: Tokenize Request")
    print(f"Prompt: {prompt[:50]}..." if len(prompt) > 50 else f"Prompt: {prompt}")
    print()
    
    try:
        response = requests.post(
            f"{SERVER_URL}/tokenize",
            json={
                "model": model,
                "prompt": prompt
            },
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        data = response.json()
        
        print("✅ Tokenize request successful!")
        print()
        print("Results:")
        print(f"  Input Tokens: {data['input_tokens']}")
        print(f"  Estimated Output Tokens: {data['estimated_output_tokens']}")
        print(f"  Estimated Cost (USD): ${data['estimated_cost_usd']}")
        print(f"  Max Tokens Remaining: {data['max_tokens_remaining']}")
        print(f"  Compression Ratio: {data['compression_ratio']}")
        print()
        print("Full Response:")
        print(json.dumps(data, indent=2))
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Tokenize request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error details: {e.response.text}")
        return None


def main():
    """Run all tests"""
    print("🧪 Testing TokenStats MCP Server")
    print(f"Server URL: {SERVER_URL}")
    print()
    
    # Test health check
    if not test_health_check():
        print("\n❌ Health check failed. Is the server running?")
        return
    
    # Test tokenize
    result = test_tokenize(TEST_PROMPT)
    
    if result:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tokenize test failed.")
        exit(1)


if __name__ == "__main__":
    main()

