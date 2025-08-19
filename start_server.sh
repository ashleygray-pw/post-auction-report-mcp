#!/bin/bash

echo "➡️  Navigating to project folder..."
pwd

echo "🔒 Activating virtual environment..."
source .venv/bin/activate

# Set default host and port for remote access
export MCP_HOST=${MCP_HOST:-"0.0.0.0"}
export MCP_PORT=${MCP_PORT:-"8000"}

echo "🧹 Cleaning up old ports..."
lsof -ti :${MCP_PORT} | xargs kill -9 2>/dev/null
lsof -ti :6277 | xargs kill -9 2>/dev/null
lsof -ti :6274 | xargs kill -9 2>/dev/null

echo "🚀 Launching MCP server on ${MCP_HOST}:${MCP_PORT} for remote access..."
python databricks_mcp.py

