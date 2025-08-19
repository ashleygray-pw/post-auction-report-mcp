#!/bin/bash

# Script to start the MCP server for remote access
# Usage: ./start_remote_server.sh [host] [port]
# Example: ./start_remote_server.sh 192.168.1.100 8000

# Set host and port from command line arguments or use defaults
export MCP_HOST=${1:-"0.0.0.0"}
export MCP_PORT=${2:-"8000"}

echo "➡️  Navigating to project folder..."
pwd

echo "🔒 Activating virtual environment..."
source .venv/bin/activate

echo "🧹 Cleaning up old ports..."
lsof -ti :${MCP_PORT} | xargs kill -9 2>/dev/null

echo "🌐 Starting MCP server for REMOTE access..."
echo "   Host: ${MCP_HOST}"
echo "   Port: ${MCP_PORT}"
echo "   Access URL: http://${MCP_HOST}:${MCP_PORT}"
echo ""
echo "📝 To connect from Claude Desktop, update your config with:"
echo "   Host: $(hostname -I | awk '{print $1}') (or your public IP)"
echo "   Port: ${MCP_PORT}"
echo ""

python databricks_mcp.py