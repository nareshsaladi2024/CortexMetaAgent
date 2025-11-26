"""
Global Configuration for CortexMetaAgent Agents and MCP Servers

This module provides centralized configuration for all agents and services.
Configuration values are read from environment variables with sensible defaults.

Environment Variables:
    AGENT_MODEL: Model name for all agents (default: "gemini-2.5-flash-lite")
    MCP_TOKENSTATS_URL: URL for mcp-tokenstats server (default: "http://localhost:8000")
    MCP_AGENT_INVENTORY_URL: URL for mcp-agent-inventory server (default: "http://localhost:8001")
    MCP_REASONING_COST_URL: URL for mcp-reasoning-cost server (default: "http://localhost:8002")
    GOOGLE_CLOUD_PROJECT: Google Cloud project ID
    GOOGLE_CLOUD_LOCATION: Google Cloud location (default: "us-central1")
    GOOGLE_APPLICATION_CREDENTIALS: Path to service account JSON file
    GOOGLE_API_KEY: Gemini API key for token counting
"""

import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file if it exists
load_dotenv()


# =============================================================================
# Agent Configuration
# =============================================================================

# Default model for all agents
# Can be overridden via AGENT_MODEL environment variable
AGENT_MODEL: str = os.environ.get("AGENT_MODEL", "gemini-2.5-flash-lite")

# Supported models:
# - gemini-2.5-flash-lite (default, fast, cost-effective)
# - gemini-2.5-flash
# - gemini-2.5-pro
# - gemini-1.5-flash
# - gemini-1.5-pro


# =============================================================================
# MCP Server URLs
# =============================================================================

MCP_TOKENSTATS_URL: str = os.environ.get("MCP_TOKENSTATS_URL", "http://localhost:8000")
MCP_AGENT_INVENTORY_URL: str = os.environ.get("MCP_AGENT_INVENTORY_URL", "http://localhost:8001")
MCP_REASONING_COST_URL: str = os.environ.get("MCP_REASONING_COST_URL", "http://localhost:8002")


# =============================================================================
# Google Cloud Configuration
# =============================================================================

GOOGLE_CLOUD_PROJECT: Optional[str] = os.environ.get("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION: str = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_API_KEY: Optional[str] = os.environ.get("GOOGLE_API_KEY")


# =============================================================================
# MCP Server Ports (for running servers)
# =============================================================================

PORT_TOKENSTATS: int = int(os.environ.get("PORT_TOKENSTATS", os.environ.get("PORT", "8000")))
PORT_AGENT_INVENTORY: int = int(os.environ.get("PORT_AGENT_INVENTORY", os.environ.get("PORT", "8001")))
PORT_REASONING_COST: int = int(os.environ.get("PORT_REASONING_COST", os.environ.get("PORT", "8002")))


# =============================================================================
# Helper Functions
# =============================================================================

def get_agent_model() -> str:
    """Get the configured agent model name"""
    return AGENT_MODEL


def get_mcp_tokenstats_url() -> str:
    """Get the mcp-tokenstats server URL"""
    return MCP_TOKENSTATS_URL


def get_mcp_agent_inventory_url() -> str:
    """Get the mcp-agent-inventory server URL"""
    return MCP_AGENT_INVENTORY_URL


def get_mcp_reasoning_cost_url() -> str:
    """Get the mcp-reasoning-cost server URL"""
    return MCP_REASONING_COST_URL


def print_config():
    """Print current configuration (useful for debugging)"""
    print("=" * 60)
    print("CortexMetaAgent Configuration")
    print("=" * 60)
    print(f"Agent Model: {AGENT_MODEL}")
    print(f"MCP TokenStats URL: {MCP_TOKENSTATS_URL}")
    print(f"MCP Agent Inventory URL: {MCP_AGENT_INVENTORY_URL}")
    print(f"MCP Reasoning Cost URL: {MCP_REASONING_COST_URL}")
    print(f"Google Cloud Project: {GOOGLE_CLOUD_PROJECT or 'Not set'}")
    print(f"Google Cloud Location: {GOOGLE_CLOUD_LOCATION}")
    print(f"Google Application Credentials: {GOOGLE_APPLICATION_CREDENTIALS or 'Not set'}")
    print(f"Google API Key: {'Set' if GOOGLE_API_KEY else 'Not set'}")
    print("=" * 60)


if __name__ == "__main__":
    # Print configuration when run directly
    print_config()

